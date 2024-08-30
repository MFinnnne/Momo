import logging
import sqlite3

from util import singleton
from datetime import datetime


class Car:
    def __init__(self, db_name='car_data.db'):
        # Initialize connection to SQLite database
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Create the CarData table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS CarData (
            id INTEGER PRIMARY KEY,
            active BOOLEAN,
            aiDetected INTEGER,
            aiDetectedDesc TEXT,
            carColor INTEGER,
            carColorDesc TEXT,
            carImage TEXT,
            carModel INTEGER,
            carModelName TEXT,
            compliance INTEGER,
            complianceDesc TEXT,
            createTime TEXT,
            deleted BOOLEAN,
            merchantDesc TEXT,
            merchantId INTEGER,
            merchantName TEXT,
            plateNumber TEXT UNIQUE,
            sourceCountry TEXT,
            sourceCountryDesc TEXT,
            updateTime TEXT
        )
        ''')
        self.conn.commit()

    def insert_data(self, data):
        # Insert new car data into the table
        self.cursor.execute('''
        INSERT INTO CarData (active, aiDetected, aiDetectedDesc, carColor, carColorDesc, carImage, 
                             carModel, carModelName, compliance, complianceDesc, createTime, deleted, 
                             merchantDesc, merchantId, merchantName, plateNumber, sourceCountry, 
                             sourceCountryDesc, updateTime)
        VALUES (:active, :aiDetected, :aiDetectedDesc, :carColor, :carColorDesc, :carImage, 
                :carModel, :carModelName, :compliance, :complianceDesc, :createTime, :deleted, 
                :merchantDesc, :merchantId, :merchantName, :plateNumber, :sourceCountry, 
                :sourceCountryDesc, :updateTime)
        ''', data)
        self.conn.commit()

    def update_data_by_id(self, id, data):
        # Update car data in the table based on id
        self.cursor.execute('''
        UPDATE CarData
        SET active = :active, aiDetected = :aiDetected, aiDetectedDesc = :aiDetectedDesc, carColor = :carColor, 
            carColorDesc = :carColorDesc, carImage = :carImage, carModel = :carModel, carModelName = :carModelName, 
            compliance = :compliance, complianceDesc = :complianceDesc, createTime = :createTime, deleted = :deleted, 
            merchantDesc = :merchantDesc, merchantId = :merchantId, merchantName = :merchantName, 
            plateNumber = :plateNumber, sourceCountry = :sourceCountry, sourceCountryDesc = :sourceCountryDesc, 
            updateTime = :updateTime
        WHERE id = :id
        ''', {**data, "id": id})
        self.conn.commit()

    def delete_data_by_id(self, id):
        # Delete car data from the table based on id
        self.cursor.execute('DELETE FROM CarData WHERE id = ?', (id,))
        self.conn.commit()

    def retrieve_data_by_plate(self, plateNumber):
        # Retrieve car data from the table based on plate number
        self.cursor.execute('SELECT * FROM CarData WHERE plateNumber = ?', (plateNumber,))
        return self.cursor.fetchall()

    def upsert_data_by_plate_and_update_time(self, data_list):
        # Batch insert or update based on plateNumber and updateTime
        for data in data_list:
            logging.info("车辆信息插入：{}".format(data))
            plateNumber = data.get("plateNumber")
            updateTime = data.get("updateTime")

            # Check if a record with the given plate number exists
            self.cursor.execute('SELECT id, updateTime FROM CarData WHERE plateNumber = ?', (plateNumber,))
            result = self.cursor.fetchone()

            # If record exists, compare updateTime
            if result:
                id, existing_update_time = result
                # If updateTime is empty or doesn't exist, insert the new data
                if not existing_update_time or not updateTime:
                    self.insert_data(data)
                else:
                    # Compare updateTime if both exist
                    existing_time = datetime.strptime(existing_update_time, "%Y-%m-%d %H:%M:%S")
                    new_time = datetime.strptime(updateTime, "%Y-%m-%d %H:%M:%S")
                    # Update if the new updateTime is more recent
                    if new_time > existing_time:
                        self.update_data_by_id(id, data)
            else:
                # If no record exists, insert the new data
                self.insert_data(data)

    def close_connection(self):
        # Close the connection to the database
        self.conn.close()