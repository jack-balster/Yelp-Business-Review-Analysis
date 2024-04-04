import json
import psycopg2

def cleanStr4SQL(s):
    return s.replace("'", "''").replace("\n", " ")

def getAttributes(attributes):
    L = []
    for (attribute, value) in list(attributes.items()):
        if isinstance(value, dict):
            L += getAttributes(value)
        else:
            L.append((attribute, value))
    return L

def truncate_tables():
    
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    try:
        cur.execute("""
            TRUNCATE TABLE Review, CheckIn, Business, Users, Category, Zipcode RESTART IDENTITY CASCADE;
        """)
        conn.commit()
        print("All tables truncated successfully.")
    except psycopg2.Error as e:
        print("An error occurred while truncating tables:", e)
        conn.rollback() 
    finally:
        cur.close()
        conn.close()

def parseAndInsertPostalCodes():
    print("Parsing and inserting postal codes...")
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    postal_codes = set()
    with open('yelp_business.JSON', 'r') as f:
        line = f.readline()
        while line:
            data = json.loads(line)
            postal_code = data['postal_code']
            if postal_code:  # Check if postal_code is not empty
                postal_codes.add(postal_code)
            line = f.readline()
    
    # Insert each unique postal code into the Zipcode table
    for postal_code in postal_codes:
        try:
            sql_str = "INSERT INTO Zipcode (PostalCode) VALUES (%s) ON CONFLICT (PostalCode) DO NOTHING;"
            cur.execute(sql_str, (postal_code,))
        except psycopg2.Error as e:
            print(f"Error inserting postal code {postal_code}: ", e)
        conn.commit()

    cur.close()
    conn.close()
    print(f"Inserted {len(postal_codes)} unique postal codes.")


def int2BoolStr (value):
    if value == 0:
        return 'False'
    else:
        return 'True'
    
def getCategoryID(cur, category_name):
    cur.execute("SELECT CategoryID FROM Category WHERE CategoryName = %s LIMIT 1;", (category_name,))
    result = cur.fetchone()
    return result[0] if result else None

def parseBusinessData():
    print("Parsing businesses...")
    
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    with open('yelp_business.JSON', 'r') as f:
        line = f.readline()
        count_line = 0
        while line:
            data = json.loads(line)
            categories = data.get('categories', [])
            category_id = None
            if categories:  # If there are categories listed, get the ID for the first one
                category_id = getCategoryID(cur, categories[0])  # Simplified to use first category

            isOpenStr = int2BoolStr(data['is_open'])
            
            sql_str = ("INSERT INTO Business (BusinessID, Name, Address, City, State, PostalCode, "
                       "Stars, ReviewCount, IsOpen, numCheckins, reviewRating, CategoryID) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);")
            values = (data['business_id'], cleanStr4SQL(data['name']), cleanStr4SQL(data['address']), 
                      cleanStr4SQL(data['city']), data['state'], data['postal_code'], 
                      data['stars'], data['review_count'], isOpenStr, 0, 0.0, category_id)

            try:
                cur.execute(sql_str, values)
            except psycopg2.Error as e:
                print("Error inserting into Business", e)
            conn.commit()

            line = f.readline()
            count_line += 1

    cur.close()
    conn.close()
    print(f"Processed {count_line} lines.")



def parseUserData():
    print("Parsing users...")
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    with open('yelp_user.json', 'r') as f:
        line = f.readline()
        count_line = 0
        while line:
            data = json.loads(line)
            sql_str = ("INSERT INTO Users (UserID, Name, ReviewCount, AverageStars) "
                       "VALUES (%s, %s, %s, %s);")
            values = (data['user_id'], cleanStr4SQL(data['name']), data['review_count'], 
                      data['average_stars'])
            
            try:
                cur.execute(sql_str, values)
            except psycopg2.Error as e:
                print("Error inserting into Users", e)
            conn.commit()

            line = f.readline()
            count_line += 1

    cur.close()
    conn.close()
    print(f"Processed {count_line} lines.")


def parseAndInsertCategories():
    print("Parsing and inserting categories...")
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    # A set to keep track of unique categories
    categories = set()

    with open('yelp_business.JSON', 'r') as f:
        line = f.readline()
        while line:
            data = json.loads(line)
            if 'categories' in data:  # Ensure there are categories to process
                for category in data['categories']:
                    categories.add(category)  # Add to set to ensure uniqueness
            line = f.readline()

    # Insert each unique category into the Category table
    for category in categories:
        try:
            sql_str = "INSERT INTO Category (CategoryName) VALUES (%s) ON CONFLICT (CategoryName) DO NOTHING;"
            cur.execute(sql_str, (category,))
        except psycopg2.Error as e:
            print(f"Error inserting category {category}: ", e)
        conn.commit()

    cur.close()
    conn.close()
    print(f"Inserted {len(categories)} unique categories.")

def parseReviewData():
    print("Parsing reviews...")
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    with open('yelp_review.json', 'r') as f:  # Update the path to your JSON file
        line = f.readline()
        count_line = 0
        while line:
            data = json.loads(line)
            # Prepare the INSERT statement to add review data
            sql_str = ("INSERT INTO Review (ReviewID, UserID, BusinessID, Stars, Date, Text, Useful, Funny, Cool) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);")
            values = (data['review_id'], data['user_id'], data['business_id'], data['stars'],
                      data['date'], cleanStr4SQL(data['text']), data['useful'], data['funny'], data['cool'])
            
            try:
                cur.execute(sql_str, values)
            except psycopg2.Error as e:
                print(f"Error inserting review {data['review_id']}: ", e)
            conn.commit()

            line = f.readline()
            count_line += 1

    cur.close()
    conn.close()
    print(f"Processed {count_line} lines.")


def parseCheckInData():
    print("Parsing check-ins...")
    conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
    cur = conn.cursor()

    with open('yelp_checkin.json', 'r') as f:
        line = f.readline()
        count_line = 0
        while line:
            data = json.loads(line)
            business_id = data['business_id']
            # Each day of the week in the "time" object
            for day, times in data['time'].items():
                # Each time of day and the count of check-ins
                for time, count in times.items():
                    sql_str = ("INSERT INTO CheckIn (BusinessID, Day, Time, Count) "
                               "VALUES (%s, %s, %s, %s);")
                    values = (business_id, day, time, count)
                    
                    try:
                        cur.execute(sql_str, values)
                    except psycopg2.Error as e:
                        print(f"Error inserting check-in data for business {business_id}: ", e)
                    conn.commit()

            line = f.readline()
            count_line += 1

    cur.close()
    conn.close()
    print(f"Processed {count_line} lines.")


if __name__ == "__main__":
    truncate_tables()
    parseAndInsertPostalCodes()
    parseAndInsertCategories()
    parseBusinessData()
    parseUserData()
    parseReviewData()
    parseCheckInData()
    
