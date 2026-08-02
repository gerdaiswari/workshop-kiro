DROP TABLE IF EXISTS inventory_items;
CREATE TABLE inventory_items (
  item_id integer PRIMARY KEY,
  name varchar(100) NOT NULL,
  quantity integer NOT NULL,
  compatibility_marker varchar(32) NOT NULL
);
INSERT INTO inventory_items VALUES
  (1, 'Angular bundle', 1, 'DATA_OK_V1'),
  (2, 'Spring service', 2, 'DATA_OK_V1'),
  (3, 'Next service', 3, 'DATA_OK_V1');
