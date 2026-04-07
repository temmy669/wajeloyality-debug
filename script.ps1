$DBNAME = "giftcard_test_db"
$USERNAME = "giftcard_test_user"
$PASSWORD = "Wajesmart@2025"
$DBHOST = "203.161.55.241"

# Get all MyISAM tables
$tables = mysql -u $USERNAME -p$PASSWORD -h $DBHOST -D $DBNAME -e "SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA='$DBNAME' AND ENGINE='MyISAM';" | Select-Object -Skip 1

# Loop through tables and convert them to InnoDB
foreach ($table in $tables) {
    Write-Host "Converting $table to InnoDB..."
    mysql -u $USERNAME -p$PASSWORD -h $DBHOST -D $DBNAME -e "ALTER TABLE $table ENGINE=InnoDB;"
}

Write-Host "All tables converted successfully!"
