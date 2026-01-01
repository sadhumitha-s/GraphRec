-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS graphrec_db;
USE graphrec_db;

-- 1. Items Table
-- Stores metadata about movies/items
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Interactions Table
-- Stores the edges of the graph (User -> Item)
CREATE TABLE IF NOT EXISTS interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    timestamp BIGINT NOT NULL,
    
    -- Optimize lookup for: "Find all items user X interacted with"
    INDEX idx_user_id (user_id),
    
    -- Optimize lookup for: "Find all users who interacted with item Y"
    INDEX idx_item_id (item_id),
    
    -- Optional: Ensure a user interacts with an item only once?
    -- UNIQUE KEY uniq_user_item (user_id, item_id),
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Initial Seed Data (Optional)
-- Populates the catalog with some starting items
INSERT INTO items (id, title, category) VALUES
(101, 'The Matrix', 'Sci-Fi'),
(102, 'Inception', 'Sci-Fi'),
(103, 'The Godfather', 'Crime'),
(104, 'Toy Story', 'Animation'),
(105, 'Pulp Fiction', 'Crime'),
(106, 'Interstellar', 'Sci-Fi'),
(107, 'Finding Nemo', 'Animation'),
(108, 'Spirited Away', 'Animation'),
(109, 'The Dark Knight', 'Action')
ON DUPLICATE KEY UPDATE title=title; -- Safe insert if run multiple times