# migrate_with_auth.py
import sqlite3
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
import sys
from typing import List, Dict

SQLITE_DB = "dummy.db"

class DataMigrationWithAuth:
    def __init__(self):
        self.sqlite_conn = None
        self.supabase = None
        self.supabase_admin = None  # Service role for auth operations
        
        self.table_mapping = {
            'offered_in': 'sem_offered',
        }
        
        self.tables = [
            'users',
            'programs', 
            'courses',
            'tags',
            'sems',
            'listings',
            'course_tag',
            'prereqs',
            'offered_in',
            'history',
            'ratings'
        ]
        
        self.primary_keys = {
            'users': ['id'],
            'programs': ['id'],
            'courses': ['id'],
            'tags': ['id'],
            'sems': ['name'],
            'ratings': ['id'],
            'listings': ['prog_id', 'course_id'],
            'course_tag': ['course_id', 'tag_id'],
            'prereqs': ['course_id', 'prereq_id'],
            'sem_offered': ['course_id', 'sem_name'],
            'history': ['user_id', 'course_id']
        }
        
        self.user_id_map = {}
    
    def get_supabase_table_name(self, sqlite_table: str) -> str:
        return self.table_mapping.get(sqlite_table, sqlite_table)
    
    def connect(self):
        print("Connecting to databases...")
        try:
            self.sqlite_conn = sqlite3.connect(SQLITE_DB)
            self.sqlite_conn.row_factory = sqlite3.Row
            print(f"  ✓ SQLite: {SQLITE_DB}")
            
            # Regular client (anon key)
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Admin client (service role key) - needed for auth operations
            try:
                self.supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                print(f"  ✓ Supabase REST API (with admin access)")
            except:
                print(f"  ⚠ No service key - using anon key (may have RLS issues)")
                self.supabase_admin = self.supabase
            
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            sys.exit(1)
    
    def close(self):
        if self.sqlite_conn:
            self.sqlite_conn.close()
    
    def get_columns(self, table_name: str) -> List[str]:
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    
    def sqlite_row_to_dict(self, row: sqlite3.Row, columns: List[str]) -> Dict:
        return {col: row[col] for col in columns}
    
    def create_auth_users(self, users_data: List[Dict]) -> List[Dict]:
        """Create users in Supabase Auth, then map to public.users"""
        print("  Creating auth users...")
        converted_users = []
        
        for user in users_data:
            old_id = user['id']
            username = user['username']
            
            # Create a fake email (since we don't have real emails)
            email = f"user{old_id}@example.com"
            password = f"TempPass{old_id}!123"  # Temporary password
            
            try:
                # Create auth user using admin client
                auth_response = self.supabase_admin.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True  # Auto-confirm email
                })
                
                new_uuid = auth_response.user.id
                self.user_id_map[old_id] = new_uuid
                
                # Prepare user data for public.users table
                converted_users.append({
                    'id': new_uuid,
                    'username': username,
                    'bio': user.get('bio'),
                    'created_at': user.get('created_at')
                })
                
                print(f"    ✓ Created user {old_id} → {new_uuid} ({email})")
                
            except Exception as e:
                # User might already exist
                if 'already been registered' in str(e):
                    print(f"    ⚠ User {email} already exists, skipping")
                else:
                    print(f"    ✗ Error creating user {old_id}: {e}")
        
        return converted_users
    
    def convert_foreign_keys(self, table_name: str, data: List[Dict]) -> List[Dict]:
        """Convert foreign key user_ids to UUIDs"""
        if not data or 'user_id' not in data[0].keys():
            return data
        
        converted = []
        for row in data:
            if 'user_id' in row and row['user_id'] in self.user_id_map:
                row['user_id'] = self.user_id_map[row['user_id']]
                converted.append(row)
            else:
                print(f"    ⚠ Skipping row with unmapped user_id: {row.get('user_id')}")
        
        return converted
    
    def upsert_table(self, sqlite_table: str) -> bool:
        supabase_table = self.get_supabase_table_name(sqlite_table)
        
        print(f"\n{sqlite_table}:", end="")
        if sqlite_table != supabase_table:
            print(f" → {supabase_table}")
        else:
            print()
        
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
        count = sqlite_cursor.fetchone()[0]
        
        if count == 0:
            print(f"  ⚠ Empty table, skipping")
            return True
        
        print(f"  Rows to upsert: {count}")
        
        sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
        rows = sqlite_cursor.fetchall()
        
        columns = self.get_columns(sqlite_table)
        data = [self.sqlite_row_to_dict(row, columns) for row in rows]
        
        # Special handling for users table
        if sqlite_table == 'users':
            data = self.create_auth_users(data)
            if not data:
                print(f"  ✗ No users to insert")
                return False
        elif sqlite_table in ['history', 'ratings']:
            data = self.convert_foreign_keys(sqlite_table, data)
            if not data:
                print(f"  ⚠ No data after foreign key conversion")
                return True
        
        pk_columns = self.primary_keys.get(supabase_table, ['id'])
        
        try:
            batch_size = 1000
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                # Use admin client for users table
                client = self.supabase_admin if sqlite_table == 'users' else self.supabase
                
                response = client.table(supabase_table).upsert(
                    batch,
                    on_conflict=','.join(pk_columns)
                ).execute()
                
                print(f"  → Processed {len(batch)} rows (batch {i//batch_size + 1})")
            
            print(f"  ✓ Upserted {len(data)} rows")
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def verify(self):
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        all_ok = True
        
        for sqlite_table in self.tables:
            supabase_table = self.get_supabase_table_name(sqlite_table)
            
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            try:
                response = self.supabase.table(supabase_table).select('*', count='exact').execute()
                supabase_count = response.count
            except Exception as e:
                print(f"✗ {sqlite_table:15s}: Error - {e}")
                all_ok = False
                continue
            
            if supabase_count >= sqlite_count:
                status = "✓"
            else:
                status = "⚠"
                all_ok = False
            
            display_name = f"{sqlite_table}→{supabase_table}" if sqlite_table != supabase_table else sqlite_table
            print(f"{status} {display_name:25s}: Local={sqlite_count:4d}, Supabase={supabase_count:4d}")
        
        return all_ok
    
    def run(self):
        print("="*60)
        print("MIGRATING WITH AUTH USER CREATION")
        print("="*60)
        
        self.connect()
        
        print("\n" + "="*60)
        print("UPSERTING TABLES")
        print("="*60)
        
        success = 0
        for table in self.tables:
            if self.upsert_table(table):
                success += 1
        
        if self.user_id_map:
            print("\n" + "="*60)
            print("USER ID MAPPING (saved to user_mapping.txt)")
            print("="*60)
            
            # Save mapping to file
            with open('user_mapping.txt', 'w') as f:
                f.write("Old_ID,New_UUID,Email\n")
                for old_id, new_uuid in self.user_id_map.items():
                    email = f"user{old_id}@example.com"
                    f.write(f"{old_id},{new_uuid},{email}\n")
                    if old_id <= 10:
                        print(f"  {old_id} → {new_uuid} ({email})")
            
            if len(self.user_id_map) > 10:
                print(f"  ... and {len(self.user_id_map) - 10} more (see user_mapping.txt)")
        
        verified = self.verify()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Successfully migrated: {success}/{len(self.tables)} tables")
        
        if verified:
            print("\n✓ Migration complete!")
            print("\nIMPORTANT: Users created with temporary passwords:")
            print("  - Email pattern: user{id}@example.com")
            print("  - Password pattern: TempPass{id}!123")
            print("  - Users should reset their passwords")
        else:
            print("\n⚠ Some issues occurred. Check above.")
        
        self.close()

if __name__ == "__main__":
    print("\n⚠️  AUTH USER MIGRATION")
    print("This will:")
    print("  1. Create auth users in Supabase Auth")
    print("  2. Map old integer IDs to new UUIDs")
    print("  3. Migrate all data with proper foreign keys")
    print("\nYou need SUPABASE_SERVICE_KEY in your .env file!")
    
    response = input("\nProceed? (yes/no): ").lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled")
        sys.exit(0)
    
    migration = DataMigrationWithAuth()
    migration.run()