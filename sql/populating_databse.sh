#!/bin/bash

# Configuration
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_USER="root"
DB_PASS="instructor"
DB_NAME="project"

# List of all your SQL scripts in order
# Make sure these files are in the same directory as this script
SQL_FILES=(
    "0_create_tables.sql"
    "1_populate_clinical.sql"
    "2_populate_mutations.sql"
    "3_insert_polya_data.sql"
    "4_insert_capture_data.sql"
    "5_insert_cna_data.sql"
)

echo "Connecting to database $DB_NAME..."

for sql_file in "${SQL_FILES[@]}"; do
    if [ -f "$sql_file" ]; then
        echo "Executing $sql_file..."
        
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$sql_file"
        
        if [ $? -eq 0 ]; then
            echo "Successfully imported $sql_file"
        else
            echo "Error: Failed to import $sql_file. Stopping."
            exit 1
        fi
    else
        echo "Warning: File $sql_file not found. Skipping."
    fi
done

echo "Database population complete."