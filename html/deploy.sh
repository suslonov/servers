aws s3 sync --delete CV s3://r-synergy.com/CV

aws cloudfront create-invalidation --distribution-id E1OYCYZ139X6W6 --paths "/*"
