ordered_itsa_ts_fields = [
    "Bank_account",  # boolean
    "Bank_reference",  # string
    "Children",  # string
    "Citizenship",  # string
    "Country",  # string
    "Credit_card_holder",  # boolean
    "Credit_history",  # boolean (new)
    "Date_of_birth",  # date
    "Education",  # string
    "Employment_status",  # string
    "Has_license",  # boolean
    "Identification",  # string
    "Income",  # string
    "Income_source_declared",  # boolean
    "Insurance",  # boolean
    "Investor",  # boolean
    "Marital_status",  # string
    "Occupation",  # string (new)
    "Phone",  # boolean
    "Proof_of_residence",  # boolean
    "Site",  # string   (new)
    "Social_network_account",  # string
    "Stable_income",  # boolean (new)
    "Stake",  # decimal
    "ZIP_code",  # string
]

identification = ["National_ID", "Passport",
                  "Not_provided", "False_documentation"]

education = ["PhD_Doctorate", "Master", "Bachelor",
             "Secondary", "Elementary", "Not_educated"]

employment_status = ["Employed", "Retired",
                     "Self_employed", "Student", "None", "Unemployed"]

income = ["$32000+", "$16000-$32000", "$8000-$16000",
          "$4000-$8000", "$2000-$4000", "$1000-$2000", "$0-$1000", "None"]

marital_status = ["Married", "Permament_relationship", "Single"]

children = ["Have_grandchildren", "Raising_children", "None"]

countries = [
    "Singapore", "SG", "SGP",
    "United States of America", "US", "USA",
    "Malaysia", "MY", "MYS",
    "Oman", "OM", "OMN",
    "Estonia", "EE", "EST",
    "Mauritius", "MU", "MUS",
    "Australia", "AU", "AUS",
    "France", "FR", "FRA",
    "Georgia", "GE", "GEO",
    "Canada", "CA", "CAN",
    "Russian Federation", "RU", "RUS",
    "Japan", "JP", "JPN",
    "Norway", "NO", "NOR",
    "Gibraltar", "GI", "GIB",
    "United Kingdom", "GB", "GBR",
    "Republic of Korea", "KR", "KOR",
    "Egypt", "EG", "EGY",
    "Netherlands", "NL", "NLD",
    "Finland", "FI", "FIN",
    "Sweden", "SE", "SWE",
    "Switzerland", "CH", "CHE",
    "New Zealand", "NZ", "NZL",
    "Israel", "IL", "ISR",
    "Latvia", "LV", "LVA",
    "Thailand", "TH", "THA",
    "India", "IN", "IND",
    "Germany", "DE", "DEU",
    "Qatar", "QA", "QAT",
    "Ireland", "IE", "IRL",
    "Belgium", "BE", "BEL",
    "Mexico", "MX", "MEX",
    "Uruguay", "UY", "URY",
    "Austria", "AT", "AUT",
    "Italy", "IT", "ITA",
    "China", "CN", "CHN",
    "Hong Kong", "HK", "HKG",
    "Macao", "MO", "MAC",
    "Taiwan, Province of China", "TW", "TWN",
    "Poland", "PL", "POL",
    "Denmark", "DK", "DNK",
    "Czech Republic", "CZ", "CZE",
    "Luxembourg", "LU", "LUX",
    "Rwanda", "RW", "RWA",
    "Philippines", "PH", "PHL",
    "Brazil", "BR", "BRA",
    "Belarus", "BY", "BLR",
    "Tunisia", "TN", "TUN",
    "Croatia", "HR", "HRV",
    "Romania", "RO", "ROU",
    "Turkey", "TR", "TUR",
    "Bulgaria", "BG", "BGR",
    "Kenya", "KE", "KEN",
    "Colombia", "CO", "COL",
    "Nigeria", "NG", "NGA",
    "Saudi Arabia", "SA", "SAU",
    "United Arab Emirates", "AE", "ARE",
    "Azerbaijan", "AZ", "AZE",
    "Morocco", "MA", "MAR",
    "Uganda", "UG", "UGA",
    "Hungary", "HU", "HUN",
    "Korea, Democratic People's Republic of", "KP", "PRK",
    "Bangladesh", "BD", "BGD",
    "Brunei Darussalam", "BN", "BRN",
    "Spain", "ES", "ESP",
    "Macedonia, the Former Yugoslav Republic of", "MK", "MKD",
    "Portugal", "PT", "PRT",
    "Lithuania", "LT", "LTU",
    "South Africa", "ZA", "ZAF",
    "Ukraine", "UA", "UKR",
    "Iran, Islamic Republic of", "IR", "IRN",
    "Cyprus", "CY", "CYP",
    "Panama", "PA", "PAN",
    "Argentina", "AR", "ARG",
    "Greece", "GR", "GRC",
    "Bahrain", "BH", "BHR",
    "Ecuador", "EC", "ECU",
    "Pakistan", "PK", "PAK",
    "Algeria", "DZ", "DZA",
    "Botswana", "BW", "BWA",
    "Indonesia", "ID", "IDN",
    "Montenegro", "ME", "MNE",
    "Sri Lanka", "LK", "LKA",
    "Moldova", "MD", "MDA",
    "Cote D'Ivoire", "CI", "CIV",
    "Cameroon", "CM", "CMR",
    "Malta", "MT", "MLT",
    "Lao People's Democratic Republic", "LA", "LAO",
    "Iceland", "IS", "ISL",
    "Peru", "PE", "PER",
    "Venezuela", "VE", "VEN",
    "Chile", "CL", "CHL",
    "Slovakia", "SK", "SVK",
    "Kazakhstan", "KZ", "KAZ",
    "Slovenia", "SI", "SVN",
    "Jamaica", "JM", "JAM",
    "Costa Rica", "CR", "CRI",
    "Ghana", "GH", "GHA",
    "Paraguay", "PY", "PRY",
    "Tanzania", "TZ", "TZA",
    "Albania", "AL", "ALB",
    "Senegal", "SN", "SEN",
    "Serbia", "RS", "SRB",
    "Tajikistan", "TJ", "TJK",
    "Tonga", "TO", "TON",
    "Zambia", "ZM", "ZMB",
    "Cambodia", "KH", "KHM",
    "Jordan", "JO", "JOR",
    "Uzbekistan", "UZ", "UZB",
    "Nepal", "NP", "NPL",
    "Barbados", "BB", "BRB",
    "Sudan", "SD", "SDN",
    "Kyrgyzstan", "KG", "KGZ",
    "Guyana", "GY", "GUY",
    "Ethiopia", "ET", "ETH",
    "Myanmar", "MM", "MMR",
    "Afghanistan", "AF", "AFG",
    "Viet Nam", "VN", "VNM",
    "Syrian Arab Republic", "SY", "SYR",
    "Monaco", "MC", "MCO",
    "Mongolia", "MN", "MNG",
    "State of Palestine", "PS", "PSE",
    "Libyan Arab Jamahiriya", "LY", "LBY",
    "Fiji", "FJ", "FJI",
    "Togo", "TG", "TGO",
    "Burkina Faso", "BF", "BFA",
    "El Salvador", "SV", "SLV",
    "Mozambique", "MZ", "MOZ",
    "Bhutan", "BT", "BTN",
    "Armenia", "AM", "ARM",
    "Liechtenstein", "LI", "LIE",
    "Zimbabwe", "ZW", "ZWE",
    "Saint Vincent and the Grenadines", "VC", "VCT",
    "Seychelles", "SC", "SYC",
    "Belize", "BZ", "BLZ",
    "Antigua and Barbuda", "AG", "ATG",
    "San Marino", "SM", "SMR",
    "Lebanon", "LB", "LBN",
    "Niger", "NE", "NER",
    "Madagascar", "MG", "MDG",
    "Dominican Republic", "DO", "DOM",
    "Suriname", "SR", "SUR",
    "Liberia", "LR", "LBR",
    "Mauritania", "MR", "MRT",
    "Nicaragua", "NI", "NIC",
    "Sierra Leone", "SL", "SLE",
    "Nauru", "NR", "NRU",
    "Gabon", "GA", "GAB",
    "Bahamas", "BS", "BHS",
    "Gambia", "GM", "GMB",
    "Vanuatu", "VU", "VUT",
    "Turkmenistan", "TM", "TKM",
    "Kiribati", "KI", "KIR",
    "Bolivia", "BO", "BOL",
    "Burundi", "BI", "BDI",
    "Bosnia and Herzegovina", "BA", "BIH",
    "Grenada", "GD", "GRD",
    "Guatemala", "GT", "GTM",
    "Kuwait", "KW", "KWT",
    "Djibouti", "DJ", "DJI",
    "Trinidad and Tobago", "TT", "TTO",
    "Solomon Islands", "SB", "SLB",
    "Lesotho", "LS", "LSO",
    "Guinea", "GN", "GIN",
    "Malawi", "MW", "MWI",
    "Angola", "AO", "AGO",
    "Eritrea", "ER", "ERI",
    "Chad", "TD", "TCD",
    "Benin", "BJ", "BEN",
    "Papua New Guinea", "PG", "PNG",
    "South Sudan", "SS", "SSD",
    "Namibia", "NAM",
    "Saint Kitts and Nevis", "KN", "KNA",
    "Mali", "ML", "MLI",
    "Cape Verde", "CV", "CPV",
    "Cuba", "CU", "CUB",
    "Andorra", "AD", "AND",
    "Maldives", "MV", "MDV",
    "Palau", "PW", "PLW",
    "Saint Lucia", "LC", "LCA",
    "Honduras", "HN", "HND",
    "Marshall Islands", "MH", "MHL",
    "Samoa", "WS", "WSM",
    "Micronesia, Federated States of", "FM", "FSM",
    "Iraq", "IQ", "IRQ",
    "Swaziland", "SZ", "SWZ",
    "Comoros", "KM", "COM",
    "Congo", "CG", "COG",
    "Congo, the Democratic Republic of the", "CD", "COD",
    "Haiti", "HT", "HTI",
    "Holy See (Vatican City State)", "VA", "VAT",
    "Sao Tome and Principe", "ST", "STP",
    "Guinea-Bissau", "GW", "GNB",
    "Somalia", "SO", "SOM",
    "Timor-Leste", "TL", "TLS",
    "Tuvalu", "TV", "TUV",
    "Dominica", "DM", "DMA",
    "Central African Republic", "CF", "CAF",
    "Yemen", "YE", "YEM",
    "NA",
    "American Samoa", "AS", "ASM",
    "Anguilla", "AI", "AIA",
    "Antarctica", "AQ", "ATA",
    "Aruba", "AW", "ABW",
    "Bermuda", "BM", "BMU",
    "Bouvet Island", "BV", "BVT",
    "British Indian Ocean Territory", "IO", "IOT",
    "Cayman Islands", "KY", "CYM",
    "Christmas Island", "CX", "CXR",
    "Cocos (Keeling) Islands", "CC", "CCK",
    "Cook Islands", "CK", "COK",
    "Equatorial Guinea", "GQ", "GNQ",
    "Falkland Islands (Malvinas)", "FK", "FLK",
    "Faroe Islands", "FO", "FRO",
    "French Guiana", "GF", "GUF",
    "French Polynesia", "PF", "PYF",
    "French Southern Territories", "TF", "ATF",
    "Greenland", "GL", "GRL",
    "Guadeloupe", "GP", "GLP",
    "Guam", "GU", "GUM",
    "Heard Island and McDonald Islands", "HM", "HMD",
    "Martinique", "MQ", "MTQ",
    "Mayotte", "YT", "MYT",
    "Montserrat", "MS", "MSR",
    "Netherlands Antilles", "AN", "ANT",
    "New Caledonia", "NC", "NCL",
    "Niue", "NU", "NIU",
    "Norfolk Island", "NF", "NFK",
    "Northern Mariana Islands", "MP", "MNP",
    "Pitcairn", "PN", "PCN",
    "Puerto Rico", "PR", "PRI",
    "Reunion", "RE", "REU",
    "Saint Helena", "SH", "SHN",
    "Saint Pierre and Miquelon", "PM", "SPM",
    "South Georgia and the South Sandwich Islands", "GS", "SGS",
    "Svalbard and Jan Mayen", "SJ", "SJM",
    "Tokelau", "TK", "TKL",
    "Turks and Caicos Islands", "TC", "TCA",
    "United States Minor Outlying Islands", "UM", "UMI",
    "Virgin Islands, British", "VG", "VGB",
    "Virgin Islands, U.S.", "VI", "VIR",
    "Wallis and Futuna", "WF", "WLF",
    "Western Sahara", "EH", "ESH",
    "Kosovo", "KV", "UNK",
    "Aland Islands", "AX", "ALA",
    "Guernsey", "GG", "GGY",
    "Jersey", "JE", "JEY",
    "Isle of Man", "IM", "IMN",
    "Saint-Barthelemy", "BL", "BLM",
    "Saint-Martin (French part)", "MF", "MAF"
]