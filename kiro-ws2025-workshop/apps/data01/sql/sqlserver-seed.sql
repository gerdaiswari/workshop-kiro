IF DB_ID(N'KiroWorkshop') IS NULL CREATE DATABASE KiroWorkshop;
GO
USE KiroWorkshop;
GO
IF OBJECT_ID(N'dbo.InventoryItems', N'U') IS NOT NULL DROP TABLE dbo.InventoryItems;
GO
CREATE TABLE dbo.InventoryItems (
  ItemId int NOT NULL PRIMARY KEY,
  Name nvarchar(100) NOT NULL,
  Quantity int NOT NULL,
  CompatibilityMarker varchar(32) NOT NULL
);
INSERT dbo.InventoryItems VALUES
  (1, N'Angular bundle', 1, 'DATA_OK_V1'),
  (2, N'Spring service', 2, 'DATA_OK_V1'),
  (3, N'Next service', 3, 'DATA_OK_V1');
GO
