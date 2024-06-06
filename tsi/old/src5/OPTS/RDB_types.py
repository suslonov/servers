import rocksdb
import itertools
from . import parameters as parms
#import parameters as parms

############################################################
######       Quick methods and non-trivial options       ###
############################################################


def b_to_str(byte_in: bytes):
    if byte_in is None:
        return "None"
    else:
        return byte_in.decode(encoding=parms.encoding)


def str_to_b(str_in: str):
    return str_in.encode(encoding=parms.encoding)


def default_db_options(uid_length=parms.uid_length):
    opts = rocksdb.Options()
    opts.create_if_missing = True
    opts.prefix_extractor = StaticPrefix(uid_length)
    opts.max_open_files = 300000
    opts.write_buffer_size = 67108864
    opts.max_write_buffer_number = 3
    opts.target_file_size_base = 67108864

    opts.table_factory = rocksdb.BlockBasedTableFactory(
        filter_policy=rocksdb.BloomFilterPolicy(10),
        block_cache=rocksdb.LRUCache(2 * (1024 ** 3)),
        block_cache_compressed=rocksdb.LRUCache(500 * (1024 ** 2)))
    return opts


##########################################
#####      Working parts             #####
##########################################


class StaticPrefix(rocksdb.interfaces.SliceTransform):
    def __init__(self, uid_length: int):
        self.uid_length = uid_length

    def name(self):
        wrd = "uid_length_" + str(self.uid_length) + "_prefix_extractor"
        return str_to_b(wrd)

    def transform(self, src):
        return (0, self.uid_length)

    def in_domain(self, src):
        return len(src) >= self.uid_length

    def in_range(self, dst):
        return len(dst) == self.uid_length


#


class CotiRocksUsrDB:
    '''Note that here the keys are purely the uid's - 
    There is no danger of overwriting the db entry as the userID's should be unique.
    If necessary checks can be put in place to ensure this.  '''

    def __init__(self, dbname: str, ordered_string_parms: list, allow_updating: bool,  options="default"):
        if options == "default":
            options = default_db_options()

        self.__db = rocksdb.DB(dbname, options)
        self.parm_list = ordered_string_parms
        self.allow_updating = allow_updating

    def __get(self, key: str):
        return b_to_str(self.__db.get(str_to_b(key)))

    def __put(self, key: str, value: str):
        self.__db.put(str_to_b(key), str_to_b(value))

    def check_if_usr_in_db(self, user_ID: str):
        bytestring = self.__db.get(str_to_b(user_ID))
        if bytestring is None:
            return False
        else:
            return True

    #

    def read_usr_parms_from_db(self, user_ID: str):
        user_info = self.__get(user_ID)
        if user_info == "None":
            raise Exception("user requested not in DB")
        else:
            parms_array = user_info.split(parms.seperator)
            user_parameters = dict()
            counter = 0
            # Note that here everything will be strings
            for parm in parms_array:
                user_parameters[self.parm_list[counter]] = parm
                counter += 1
            return user_parameters

    #

    def update_write_user_parms_to_db(self, user_params: dict, allow_updating=None):
        user_id = user_params["user_ID"]
        user_info = self.__get(user_id)
        if allow_updating is None:
            allow_updating = self.allow_updating
        if (not allow_updating) and (user_info != "None"):
            message = "Tried to update a user_ID in database when the option for this was expressly forbidden - IGNORING."
            print(message)
            return message
        # complementary data to make up for any missing values etc.
        complementary_data = dict()
        if len(user_params) < len(self.parm_list):
            complementary_data = parms.default_user if user_info == "None"\
                else self.read_usr_parms_from_db(user_id)
        user_info = ""
        counter = 0
        #
        for usr_parm in self.parm_list:
            if usr_parm == "user_ID":
                continue
            if counter != 0:
                # adds commas before everything except at the front
                user_info += parms.seperator
            counter += 1
            #
            if usr_parm not in user_params:
                print(
                    "WARNING - adding value for missing user parameter (from db or default).")
                user_info += str(complementary_data[usr_parm])
            else:
                user_info += str(user_params[usr_parm])
        # encoding everything as utf-8 for the sake of robustness when transitioning between
        # different versions of python etc.
        self.__put(user_id, user_info)


class CotiRocksTxnDB:
    '''Here the key value is sender_ID,time (here the , is from params.separator)'''
    '''Alternatively the key value can be the receiver_ID,time
    
    This is done for the sake of easily checking the differential of the account balance, as
    loading the entire db to check when a specific user recieved funds is unreasonable'''

    def __init__(self, dbname: str, db_id_by: str, options="default"):
        if options == "default":
            options = default_db_options()
        self.__db = rocksdb.DB(dbname, options)
        self.db_id_by = db_id_by

    #
    def __get(self, key: str):
        return b_to_str(self.__db.get(str_to_b(key)))

    def __put(self, key: str, value: str):
        self.__db.put(str_to_b(key), str_to_b(value))

    def __get_all_for_uid(self, user_ID: str):
        uid = str_to_b(user_ID)
        it = self.__db.iteritems()
        it.seek(uid)
        u_info = dict(itertools.takewhile(
            lambda item: item[0].startswith(uid), it))
        return u_info

    #

    def get_usr_txn_history(self, user_ID: str):
        byte_dict = self.__get_all_for_uid(user_ID)
        hist = dict()
        for txn_parm in parms.ordered_txn_parms:
            if txn_parm != self.db_id_by:
                hist[txn_parm] = []

        for key in sorted(list(byte_dict.keys()), reverse=True):
            info = byte_dict[key]
            time = b_to_str(key).split(parms.seperator)[1]
            txn_info = b_to_str(info).split(parms.seperator)
            hist["transaction_time"] += [time]
            counter = 0
            for txn_parm in parms.ordered_txn_parms:
                if txn_parm != self.db_id_by and txn_parm != "transaction_time":
                    hist[txn_parm] += [txn_info[counter]]
                    counter += 1
        return hist

    #

    def add_txn_to_db(self, txn: dict):
        send_rec_ID = txn[self.db_id_by]
        time = txn["transaction_time"]
        key = send_rec_ID + parms.seperator + str(time)
        txn_info = ""
        for txn_parm in parms.ordered_txn_parms:
            if txn_parm != self.db_id_by and txn_parm != "transaction_time":
                if len(txn_info) > 0:
                    txn_info += parms.seperator
                #
                txn_info += str(txn[txn_parm])
        self.__put(key, txn_info)
