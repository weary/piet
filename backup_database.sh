mkdir -p /hd/piet/backup
TARGET="/hd/piet/backup/piet_`date +%Y%m%d`.db.bz2"
sqlite3 /hd/piet/piet.db ".dump" | bzip2 -zc > $TARGET
