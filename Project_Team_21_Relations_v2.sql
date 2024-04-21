CREATE TABLE Zipcode (
    PostalCode VARCHAR(10) PRIMARY KEY,
    Population INT,
    AverageIncome FLOAT
);

CREATE TABLE Category (
    CategoryID SERIAL PRIMARY KEY,
    CategoryName VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE Business (
    BusinessID VARCHAR(255) PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Address VARCHAR(255),
    City VARCHAR(255),
    State VARCHAR(2),
    PostalCode VARCHAR(10),
	Stars FLOAT,
    ReviewCount INT,
    IsOpen BOOLEAN,
    numCheckins INT DEFAULT 0,
    reviewRating FLOAT DEFAULT 0.0,
	CategoryID INT,
    FOREIGN KEY (PostalCode) REFERENCES Zipcode(PostalCode),
	FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);


CREATE TABLE Users (
    UserID VARCHAR(255) PRIMARY KEY,
    Name VARCHAR(255),
    ReviewCount INT,
    AverageStars FLOAT
);

CREATE TABLE Review (
    ReviewID VARCHAR(255) PRIMARY KEY,
    UserID VARCHAR(255),
    BusinessID VARCHAR(255),
    Stars INT,
    Date DATE,
    Text TEXT,
    Useful INT,
    Funny INT,
    Cool INT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (BusinessID) REFERENCES Business(BusinessID)
);

CREATE TABLE CheckIn (
    CheckInID SERIAL PRIMARY KEY,
    BusinessID VARCHAR(255),
    Day VARCHAR(10),
    Time VARCHAR(5),
    Count INT,
    FOREIGN KEY (BusinessID) REFERENCES Business(BusinessID)
);