CREATE DATABASE IF NOT EXISTS kiro_workshop;
USE kiro_workshop;
DROP TABLE IF EXISTS inventory_items;
CREATE TABLE inventory_items (
  item_id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  quantity INT NOT NULL,
  compatibility_marker VARCHAR(32) NOT NULL
) ENGINE=InnoDB;
INSERT INTO inventory_items VALUES
  (1, 'Angular bundle', 1, 'DATA_OK_V1'),
  (2, 'Spring service', 2, 'DATA_OK_V1'),
  (3, 'Next service', 3, 'DATA_OK_V1');
