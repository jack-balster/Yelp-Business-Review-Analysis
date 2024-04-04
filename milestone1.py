import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
import psycopg2

qtCreatorFile = "milestone1App.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class Milestone1(QMainWindow):
    def __init__(self):
        super(Milestone1, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.loadStateList()
        self.ui.stateList.currentTextChanged.connect(self.stateChanged)
        self.ui.cityList.itemSelectionChanged.connect(self.cityChanged)
        self.ui.bname.textChanged.connect(self.getBusinessNames)
        self.ui.businesses.itemSelectionChanged.connect(self.displayBusinessCity)
        self.ui.zipcodeList.itemSelectionChanged.connect(self.zipcodeChanged)

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
        state = self.ui.stateList.currentText()
        if state:
            self.ui.cityList.clear()
            sql_str = "SELECT DISTINCT city FROM business WHERE state = %s ORDER BY city;"
            results = self.executeQuery(sql_str, (state,))
            if results:
                for row in results:
                    self.ui.cityList.addItem(row[0])
                self.ui.businessTable.setRowCount(0)  # Clear business table upon state change (was getting business query error)
            else:
                print("Query failed to load cities.")
        self.ui.cityList.itemSelectionChanged.connect(self.cityChanged)  # Reconnect signal

    def cityChanged(self):
        state = self.ui.stateList.currentText()
        city = self.ui.cityList.currentItem().text() if self.ui.cityList.currentItem() else None
        if state and city:
            sql_str = "SELECT name, city, state FROM business WHERE state = %s AND city = %s ORDER BY name;"

            results = self.executeQuery(sql_str, (state, city))
            if results:
                self.updateBusinessTable(results)
            else:
                self.ui.businessTable.setRowCount(0)
                print("No businesses found for the selected city.")
        else:
            self.ui.businessTable.setRowCount(0)
        
        if city:
            self.loadZipCodes(city)

    def loadZipCodes(self, city):
        self.ui.zipcodeList.clear()
        sql_str = "SELECT DISTINCT PostalCode FROM business WHERE city = %s ORDER BY PostalCode;"
        results = self.executeQuery(sql_str, (city,))
        if results:
            for row in results:
                self.ui.zipcodeList.addItem(row[0])

    def zipcodeChanged(self):
        zipcode = self.ui.zipcodeList.currentItem().text() if self.ui.zipcodeList.currentItem() else None
        if zipcode:
            sql_str = """
            SELECT b.Name, MIN(c.CategoryName) AS CategoryName, b.PostalCode
            FROM Business b
            JOIN Category c ON b.CategoryID = c.CategoryID
            WHERE b.PostalCode = %s
            GROUP BY b.Name, b.PostalCode
            ORDER BY MIN(c.CategoryName), b.Name;
            """
            results = self.executeQuery(sql_str, (zipcode,))
            if results is not None and len(results) > 0:
                self.updateBusinessTable2(results)
            else:
                self.ui.businessTable2.setRowCount(0)
                print("No businesses found for the selected zipcode or unable to connect to database.")



    def updateBusinessTable(self, results):
        self.ui.businessTable.setRowCount(len(results))
        self.ui.businessTable.setColumnCount(3)  # name, city, state
        self.ui.businessTable.setHorizontalHeaderLabels(['Business Name', 'City', 'State'])
        for row_index, row_data in enumerate(results):
            for column_index, data in enumerate(row_data):
                self.ui.businessTable.setItem(row_index, column_index, QTableWidgetItem(str(data)))
        self.ui.businessTable.resizeColumnsToContents()


    def updateBusinessTable2(self, results):
        self.ui.businessTable2.setRowCount(len(results))
        self.ui.businessTable2.setColumnCount(3) 
        self.ui.businessTable2.setHorizontalHeaderLabels(['Category', 'Business Name', 'Postal Code'])
        for row_index, row_data in enumerate(results):
            self.ui.businessTable2.setItem(row_index, 0, QTableWidgetItem(str(row_data[1])))  # Category
            self.ui.businessTable2.setItem(row_index, 1, QTableWidgetItem(str(row_data[0])))  # Business Name
            self.ui.businessTable2.setItem(row_index, 2, QTableWidgetItem(str(row_data[2])))  # Postal Code
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
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Milestone1()
    window.show()
    sys.exit(app.exec_())
