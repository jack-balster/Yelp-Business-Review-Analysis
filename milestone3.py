import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
import psycopg2

qtCreatorFile = "milestone3App.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class Milestone1(QMainWindow):
    def __init__(self):
        super(Milestone1, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.loadStateList()
        self.ui.stateList.currentTextChanged.connect(self.stateChanged)
        self.ui.cityList.itemSelectionChanged.connect(self.cityChanged)
        self.ui.zipcodeList.itemSelectionChanged.connect(self.zipcodeChanged)
        self.ui.filterCategoriesTable.itemSelectionChanged.connect(self.categoryChanged)

    def executeQuery(self, sql_str, params=None):
        try:
            conn = psycopg2.connect("dbname='milestone1db' user='postgres' host='localhost' password='21JustJack'")
            cur = conn.cursor()
            if params:
                cur.execute(sql_str, params)
            else:
                cur.execute(sql_str)
            result = cur.fetchall()
            cur.close()
            return result
        except (Exception, psycopg2.DatabaseError) as error:
            print("Unable to connect to databse")
            return None
        finally:
            if conn is not None:
                conn.close()

    def loadStateList(self):
        self.ui.stateList.clear()
        sql_str = "SELECT DISTINCT state FROM business ORDER BY state;"
        results = self.executeQuery(sql_str)
        if results:
            for row in results:
                self.ui.stateList.addItem(row[0])
        else:
            print("Query failed to load states.")

    def stateChanged(self):
        self.ui.cityList.itemSelectionChanged.disconnect(self.cityChanged)  # Disconnect signal
        self.ui.cityList.clear()
        self.ui.zipcodeList.clear()
        state = self.ui.stateList.currentText()
        if state:
            self.ui.cityList.clear()
            sql_str = "SELECT DISTINCT city FROM business WHERE state = %s ORDER BY city;"
            results = self.executeQuery(sql_str, (state,))
            if results:
                for row in results:
                    self.ui.cityList.addItem(row[0])
                self.ui.businessTable2.setRowCount(0)  # Clear business table upon state change (was getting business query error)
            else:
                print("Query failed to load cities.")
        else:
            self.ui.cityList.clear()
        self.clearAllTables()
        self.ui.cityList.itemSelectionChanged.connect(self.cityChanged)  # Reconnect signal

    def cityChanged(self):
        state = self.ui.stateList.currentText()
        city = self.ui.cityList.currentItem().text() if self.ui.cityList.currentItem() else None
        if city:
            self.loadZipCodes(city)
        self.clearAllTables()

    def loadZipCodes(self, city):
        self.ui.zipcodeList.clear()
        sql_str = "SELECT DISTINCT PostalCode FROM business WHERE city = %s ORDER BY PostalCode;"
        results = self.executeQuery(sql_str, (city,))
        if results:
            for row in results:
                self.ui.zipcodeList.addItem(row[0])
        else:
            print("No ZIP codes found for the selected city.")

    def zipcodeChanged(self):
        zipcode = self.ui.zipcodeList.currentItem().text() if self.ui.zipcodeList.currentItem() else None
        if zipcode:
            # Query for the business details in the selected ZIP code
            business_query = """
            SELECT Name, Address, City, Stars, ReviewCount, reviewRating, numCheckins
            FROM Business
            WHERE PostalCode = %s;
            """
            business_results = self.executeQuery(business_query, (zipcode,))
            if business_results is not None and len(business_results) > 0:
                self.updateBusinessTable2(business_results)
            else:
                self.ui.businessTable2.setRowCount(0)
                print("No businesses found for the selected zipcode.")

            # Query for ZIP code information
            zip_info_query = """
            SELECT COUNT(*), zd.population, zd.medianIncome
            FROM Business b
            JOIN zipcodeData zd ON b.PostalCode = zd.zipcode
            WHERE b.PostalCode = %s
            GROUP BY zd.population, zd.medianIncome;
            """
            zip_info_results = self.executeQuery(zip_info_query, (zipcode,))
            if zip_info_results:
                self.updateZipInfoTable(zip_info_results[0])  # Passing the first row of results
            else:
                self.ui.zipInfoTable.setRowCount(0)
                print("No ZIP code info found for the selected zipcode.")

            self.updateTopCategories(zipcode)
            self.updateFilterCategories(zipcode)
            self.updatePopularBusinesses(zipcode)
            self.updateSuccessfulBusinesses(zipcode)

    def categoryChanged(self):
        selected_items = self.ui.filterCategoriesTable.selectedItems()
        if selected_items:
            category_name = selected_items[0].text()
            zipcode = self.ui.zipcodeList.currentItem().text() if self.ui.zipcodeList.currentItem() else None
            if zipcode:
                self.updateBusinessTableByCategory(zipcode, category_name)
                self.updatePopularBusinessesByCategory(zipcode, category_name)
                self.updateSuccessfulBusinessesByCategory(category_name)
    
    def updateBusinessTableByCategory(self, zipcode, category_name):
        sql_str = """
        SELECT b.Name, b.Address, b.City, b.Stars, b.ReviewCount, b.reviewRating, b.numCheckins
        FROM Business b
        JOIN Category c ON b.CategoryID = c.CategoryID
        WHERE b.PostalCode = %s AND c.CategoryName = %s;
        """
        results = self.executeQuery(sql_str, (zipcode, category_name))
        if results:
            self.updateBusinessTable2(results)
        else:
            self.ui.businessTable2.setRowCount(0)
            print("No businesses found for the selected category in the selected zipcode.")

    def updateTopCategories(self, zipcode):
        sql_str = """
        SELECT COUNT(b.BusinessID) AS numBusinesses, c.CategoryName
        FROM Business b
        JOIN Category c ON b.CategoryID = c.CategoryID
        WHERE b.PostalCode = %s
        GROUP BY c.CategoryName
        ORDER BY numBusinesses DESC;
        """
        results = self.executeQuery(sql_str, (zipcode,))
        if results:
            self.populateTopCategoriesTable(results)
        else:
            self.ui.topCategoriesTable.setRowCount(0)
            print("No categories found for the selected zipcode.")

    def populateTopCategoriesTable(self, categories):
        self.ui.topCategoriesTable.setRowCount(len(categories))
        self.ui.topCategoriesTable.setColumnCount(2)  # Two columns: number of businesses and category name
        self.ui.topCategoriesTable.setHorizontalHeaderLabels(['# Bus.', 'Category'])
        for row_index, (num_businesses, category_name) in enumerate(categories):
            self.ui.topCategoriesTable.setItem(row_index, 0, QTableWidgetItem(str(num_businesses)))
            self.ui.topCategoriesTable.setItem(row_index, 1, QTableWidgetItem(str(category_name)))
        self.ui.topCategoriesTable.resizeColumnsToContents()

    def updateFilterCategories(self, zipcode):
        sql_str = """
        SELECT DISTINCT c.CategoryName
        FROM Business b
        JOIN Category c ON b.CategoryID = c.CategoryID
        WHERE b.PostalCode = %s
        ORDER BY c.CategoryName;
        """
        results = self.executeQuery(sql_str, (zipcode,))
        if results:
            self.populateFilterCategoriesTable(results)
        else:
            self.ui.filterCategoriesTable.setRowCount(0)
            print("No categories found for the selected zipcode.")

    def populateFilterCategoriesTable(self, categories):
        self.ui.filterCategoriesTable.setRowCount(len(categories))
        self.ui.filterCategoriesTable.setColumnCount(1)  # One column for category names
        self.ui.filterCategoriesTable.setHorizontalHeaderLabels(['Category Names'])
        for row_index, (category_name,) in enumerate(categories):
            self.ui.filterCategoriesTable.setItem(row_index, 0, QTableWidgetItem(str(category_name)))
        self.ui.filterCategoriesTable.resizeColumnsToContents()

    def updateZipInfoTable(self, zip_info):
        self.ui.zipInfoTable.setRowCount(1)  # One row for the ZIP code data
        self.ui.zipInfoTable.setColumnCount(3)  # Three columns for num businesses, population, avg income
        self.ui.zipInfoTable.setHorizontalHeaderLabels(['# Bus.', 'Population', 'Avg Income'])
        self.ui.zipInfoTable.setItem(0, 0, QTableWidgetItem(str(zip_info[0])))
        self.ui.zipInfoTable.setItem(0, 1, QTableWidgetItem(str(zip_info[1])))
        self.ui.zipInfoTable.setItem(0, 2, QTableWidgetItem(str(zip_info[2])))
        self.ui.zipInfoTable.resizeColumnsToContents()

    def updatePopularBusinesses(self, zipcode):
        sql_str = """
        SELECT
            Category.CategoryName,
            Business.Name AS BusinessName,
            SUM(Business.numCheckins) AS TotalCheckIns,
            AVG(Business.reviewRating) AS AvgReviewRating,
            (0.8 * SUM(Business.numCheckins) + 0.2 * AVG(Business.reviewRating)) AS PopularityScore
        FROM
            Business
        JOIN
            Category ON Business.CategoryID = Category.CategoryID
        WHERE
            Business.PostalCode = %s
        GROUP BY
            Category.CategoryName, Business.Name
        ORDER BY
            PopularityScore DESC;
        """
        results = self.executeQuery(sql_str, (zipcode,))
        if results:
            self.populatePopularBusinessTable(results)
        else:
            self.ui.popularBusinessTable.setRowCount(0)
            print("No popular businesses found for the selected zipcode.")

    def populatePopularBusinessTable(self, businesses):
        self.ui.popularBusinessTable.setRowCount(len(businesses))
        self.ui.popularBusinessTable.setColumnCount(5)
        self.ui.popularBusinessTable.setHorizontalHeaderLabels(['Popularity Score', 'Business Name', 'Total Check-Ins', 'Average Review Rating', 'Category'])
        for row_index, (category_name, business_name, total_check_ins, avg_review_rating, popularity_score) in enumerate(businesses):
            self.ui.popularBusinessTable.setItem(row_index, 0, QTableWidgetItem(f"{popularity_score:.2f}"))  
            self.ui.popularBusinessTable.setItem(row_index, 1, QTableWidgetItem(business_name))
            self.ui.popularBusinessTable.setItem(row_index, 2, QTableWidgetItem(str(total_check_ins)))
            self.ui.popularBusinessTable.setItem(row_index, 3, QTableWidgetItem(f"{avg_review_rating:.1f}"))
            self.ui.popularBusinessTable.setItem(row_index, 4, QTableWidgetItem(category_name))
        self.ui.popularBusinessTable.resizeColumnsToContents()


    def updatePopularBusinessesByCategory(self, zipcode, category_name):
        sql_str = """
        SELECT Category.CategoryName, Business.Name, SUM(Business.numCheckins) AS TotalCheckIns, 
        AVG(Business.reviewRating) AS AvgReviewRating,
        (0.8 * SUM(Business.numCheckins) + 0.2 * AVG(Business.reviewRating)) AS PopularityScore
        FROM Business
        JOIN Category ON Business.CategoryID = Category.CategoryID
        WHERE Business.PostalCode = %s AND Category.CategoryName = %s
        GROUP BY Category.CategoryName, Business.Name
        ORDER BY PopularityScore DESC;
        """
        results = self.executeQuery(sql_str, (zipcode, category_name))
        if results:
            self.populatePopularBusinessTable(results)
        else:
            self.ui.popularBusinessTable.setRowCount(0)
            print("No popular businesses found for the selected category and zipcode.")

    def updateSuccessfulBusinessesByCategory(self, category_name):
        sql_str = """
        SELECT Category.CategoryName, Business.Name, 
        DATE_PART('year', MAX(Review.Date)) - DATE_PART('year', MIN(Review.Date)) AS LongevityYears,
        AVG(Review.Stars) AS AvgRating,
        (0.7 * (DATE_PART('year', MAX(Review.Date)) - DATE_PART('year', MIN(Review.Date))) + 0.3 * AVG(Review.Stars)) AS SuccessScore
        FROM Business
        LEFT JOIN Review ON Business.BusinessID = Review.BusinessID
        JOIN Category ON Business.CategoryID = Category.CategoryID
        WHERE Category.CategoryName = %s
        GROUP BY Category.CategoryName, Business.Name
        ORDER BY SuccessScore DESC;
        """
        results = self.executeQuery(sql_str, (category_name,))
        if results:
            self.populateSuccessfulTable(results)
        else:
            self.ui.successfulTable.setRowCount(0)
            print("No successful businesses found for the selected category.")
    def updateSuccessfulBusinesses(self, zipcode):
        sql_str = """
        SELECT
            Category.CategoryName,
            Business.Name AS BusinessName,
            DATE_PART('year', MAX(Review.Date)) - DATE_PART('year', MIN(Review.Date)) AS LongevityYears,
            AVG(Review.Stars) AS AvgRating,
            (0.7 * (DATE_PART('year', MAX(Review.Date)) - DATE_PART('year', MIN(Review.Date))) + 0.3 * AVG(Review.Stars)) AS SuccessScore
        FROM
            Business
        LEFT JOIN Review ON Business.BusinessID = Review.BusinessID
        JOIN Category ON Business.CategoryID = Category.CategoryID
        WHERE
            Business.PostalCode = %s
        GROUP BY
            Business.Name, Category.CategoryName
        ORDER BY
            SuccessScore DESC;
        """
        results = self.executeQuery(sql_str, (zipcode,))
        if results:
            self.populateSuccessfulTable(results)
        else:
            self.ui.successfulTable.setRowCount(0)
            print("No successful businesses found for the selected zipcode.")

    def populateSuccessfulTable(self, businesses):
        self.ui.successfulTable.setRowCount(len(businesses))
        self.ui.successfulTable.setColumnCount(5)
        self.ui.successfulTable.setHorizontalHeaderLabels(['Success Score', 'Business Name', 'Longevity (Years)', 'Average Rating', 'Category'])
        for row_index, (category_name, business_name, longevity_years, avg_rating, success_score) in enumerate(businesses):
            self.ui.successfulTable.setItem(row_index, 0, QTableWidgetItem(f"{success_score:.2f}"))
            self.ui.successfulTable.setItem(row_index, 1, QTableWidgetItem(business_name))
            self.ui.successfulTable.setItem(row_index, 2, QTableWidgetItem(str(longevity_years)))
            self.ui.successfulTable.setItem(row_index, 3, QTableWidgetItem(f"{avg_rating:.1f}"))
            self.ui.successfulTable.setItem(row_index, 4, QTableWidgetItem(category_name))
        self.ui.successfulTable.resizeColumnsToContents()

    def updateBusinessTable2(self, results):
        self.ui.businessTable2.setRowCount(len(results))
        self.ui.businessTable2.setColumnCount(7)
        self.ui.businessTable2.setHorizontalHeaderLabels(['Name', 'Address', 'City', 'Stars', 'Review Count', 'Avg Review Rating', 'Num of Check-Ins'])
        for row_index, row_data in enumerate(results):
            for col_index, data in enumerate(row_data):
                self.ui.businessTable2.setItem(row_index, col_index, QTableWidgetItem(str(data)))
        self.ui.businessTable2.resizeColumnsToContents()

    def getBusinessNames(self):
        self.ui.businesses.clear()
        businessname = self.ui.bname.text()
        sql_str = "SELECT name FROM business WHERE name LIKE %s ORDER BY name;"
        param = ('%' + businessname + '%',)
        try:
            results = self.executeQuery(sql_str, param)
            for row in results:
                self.ui.businesses.addItem(row[0])
        except:
            print("Query Error")
    

    def displayBusinessCity(self):
        businessname = self.ui.businesses.selectedItems()[0].text()
        sql_str = "SELECT city FROM business WHERE name = %s;"
        param = (businessname,)
        try:
            results = self.executeQuery(sql_str, param)
            self.ui.bcity.setText(results[0][0])
        except:
            print("Query Error")
        
    def clearAllTables(self):
        tables = [
            self.ui.zipInfoTable,
            self.ui.topCategoriesTable,
            self.ui.businessTable2,
            self.ui.popularBusinessTable,
            self.ui.successfulTable,
            self.ui.filterCategoriesTable
        ]
        for table in tables:
            table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Milestone1()
    window.show()
    sys.exit(app.exec_())
