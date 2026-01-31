# database.py
# This handles database operations

import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='risk_module.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
    
    def connect(self):
        # Connect to database
        print(f"Connecting to database: {self.db_name}")
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        print("Connected!\n")
    
    def create_tables(self):
        # Create tables for GPS data and risk results
        
        print("Creating tables...")
        
        # Table 1: GPS Data
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS gps_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                speed REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                stopped_seconds INTEGER NOT NULL,
                scenario TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 2: Risk Results
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gps_data_id INTEGER NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                zone_name TEXT NOT NULL,
                zone_type TEXT NOT NULL,
                crime_weight REAL NOT NULL,
                reasons TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gps_data_id) REFERENCES gps_data(id)
            )
        ''')
        
        # Table 3: Statistics
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_points INTEGER,
                safe_count INTEGER,
                low_count INTEGER,
                medium_count INTEGER,
                high_count INTEGER,
                critical_count INTEGER,
                average_risk REAL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("Tables created!\n")
    
    def insert_gps_data(self, data_list):
        # Insert GPS data into database
        
        print(f"Inserting {len(data_list)} GPS data points...")
        
        for i, data in enumerate(data_list):
            self.cursor.execute('''
                INSERT INTO gps_data 
                (latitude, longitude, speed, timestamp, stopped_seconds, scenario)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['lat'],
                data['lon'],
                data['speed'],
                data['timestamp'],
                data['stopped'],
                data['scenario']
            ))
            
            if (i + 1) % 5000 == 0:
                print(f"  Inserted {i + 1}/{len(data_list)} points")
        
        self.conn.commit()
        print(f"Inserted all {len(data_list)} points!\n")
    
    def insert_risk_result(self, gps_data_id, result, zone_info):
        # Insert risk result into database
        
        reasons = ' | '.join(result.reasons)
        
        self.cursor.execute('''
            INSERT INTO risk_results
            (gps_data_id, risk_score, risk_level, zone_name, zone_type, crime_weight, reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            gps_data_id,
            result.score,
            result.level,
            result.zone_name,
            zone_info['zone_type'],
            zone_info['crime_weight'],
            reasons
        ))
        
        self.conn.commit()
    
    def insert_risk_results_batch(self, data_list, results, zone_infos):
        # Insert all risk results at once (faster)
        
        print(f"Inserting {len(results)} risk results...")
        
        for i, (data, result, zone_info) in enumerate(zip(data_list, results, zone_infos)):
            reasons = ' | '.join(result.reasons)
            
            self.cursor.execute('''
                INSERT INTO risk_results
                (gps_data_id, risk_score, risk_level, zone_name, zone_type, crime_weight, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                i + 1,
                result.score,
                result.level,
                result.zone_name,
                zone_info['zone_type'],
                zone_info['crime_weight'],
                reasons
            ))
            
            if (i + 1) % 5000 == 0:
                print(f"  Inserted {i + 1}/{len(results)} results")
        
        self.conn.commit()
        print(f"Inserted all {len(results)} results!\n")
    
    def insert_statistics(self, total, safe, low, medium, high, critical, avg_risk):
        # Insert statistics
        
        self.cursor.execute('''
            INSERT INTO statistics
            (total_points, safe_count, low_count, medium_count, high_count, critical_count, average_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            total,
            safe,
            low,
            medium,
            high,
            critical,
            avg_risk
        ))
        
        self.conn.commit()
        print("Statistics saved!\n")
    
    def get_all_results(self):
        # Get all risk results
        
        self.cursor.execute('''
            SELECT * FROM risk_results
        ''')
        
        return self.cursor.fetchall()
    
    def get_results_by_level(self, level):
        # Get results by risk level
        
        self.cursor.execute('''
            SELECT * FROM risk_results WHERE risk_level = ?
        ''', (level,))
        
        return self.cursor.fetchall()
    
    def get_results_by_zone(self, zone_name):
        # Get results by zone name
        
        self.cursor.execute('''
            SELECT * FROM risk_results WHERE zone_name = ?
        ''', (zone_name,))
        
        return self.cursor.fetchall()
    
    def get_statistics(self):
        # Get latest statistics
        
        self.cursor.execute('''
            SELECT * FROM statistics ORDER BY generated_at DESC LIMIT 1
        ''')
        
        return self.cursor.fetchone()
    
    def get_high_risk_zones(self):
        # Get zones with most high-risk incidents
        
        self.cursor.execute('''
            SELECT zone_name, COUNT(*) as count, AVG(risk_score) as avg_risk
            FROM risk_results
            WHERE risk_level IN ('HIGH', 'CRITICAL')
            GROUP BY zone_name
            ORDER BY count DESC
        ''')
        
        return self.cursor.fetchall()
    
    def export_to_csv(self, filename, query=None):
        # Export results to CSV
        
        import csv
        
        if query is None:
            self.cursor.execute('SELECT * FROM risk_results')
        else:
            self.cursor.execute(query)
        
        rows = self.cursor.fetchall()
        cols = [description[0] for description in self.cursor.description]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)
        
        print(f"Exported {len(rows)} rows to {filename}\n")
    
    def delete_all_data(self):
        # Delete all data (for fresh start)
        
        self.cursor.execute('DELETE FROM risk_results')
        self.cursor.execute('DELETE FROM gps_data')
        self.cursor.execute('DELETE FROM statistics')
        self.conn.commit()
        print("All data deleted!\n")
    
    def close(self):
        # Close database connection
        
        if self.conn:
            self.conn.close()
            print("Database closed!\n")
    
    def show_summary(self):
        # Show database summary
        
        self.cursor.execute('SELECT COUNT(*) FROM gps_data')
        gps_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM risk_results')
        risk_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            SELECT risk_level, COUNT(*) FROM risk_results
            GROUP BY risk_level
        ''')
        level_counts = self.cursor.fetchall()
        
        print("\n" + "="*50)
        print("DATABASE SUMMARY")
        print("="*50)
        print(f"GPS Data Points: {gps_count}")
        print(f"Risk Results: {risk_count}")
        print("\nRisk Level Distribution:")
        for level, count in level_counts:
            print(f"  {level}: {count}")
        print("="*50 + "\n")