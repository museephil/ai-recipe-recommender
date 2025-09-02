-- Users Table
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone_number VARCHAR(15),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email, password_hash, phone_number) VALUES
('Mary Achieng', 'mary.achieng@example.com', 'hashed_pw1', '254722123456'),
('Joseph Mwangi', 'joseph.mwangi@example.com', 'hashed_pw2', '254733987654'),
('Faith Wanjiku', 'faith.wanjiku@example.com', 'hashed_pw3', '234712345678'),
('Brian Otieno', 'brian.otieno@example.com', 'hashed_pw4', '234798123456'),
('Mercy Naliaka', 'mercy.naliaka@example.com', 'hashed_pw5', '22475123987');

-- Recipes Table
CREATE TABLE recipes (
  recipe_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  ingredients TEXT NOT NULL,
  steps TEXT NOT NULL,
  created_by INT,
  FOREIGN KEY (created_by) REFERENCES users(user_id)
);

INSERT INTO recipes (title, ingredients, steps, created_by) VALUES
('Ugali with Sukuma Wiki', 'maize flour, sukuma wiki, salt, water', 'Boil water, add flour, stir until firm, fry sukuma with onions and serve.', 1),
('Chapati with Beans Stew', 'wheat flour, beans, onions, tomatoes, oil', 'Make dough, roll chapatis, fry, cook beans stew, serve together.', 2),
('Pilau Rice', 'rice, beef, onions, garlic, pilau masala', 'Fry onions and spices, add beef, add rice and water, cook until ready.', 3),
('Mukimo', 'potatoes, maize, pumpkin leaves, beans', 'Boil potatoes and maize, mash together with leaves and beans, serve hot.', 4),
('Fish Curry', 'tilapia fish, onions, tomatoes, coconut milk, spices', 'Fry onions and spices, add tomatoes, add fish, simmer with coconut milk.', 5);

-- Payments Table
CREATE TABLE payments (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  amount DECIMAL(10,2) NOT NULL,
  payment_method VARCHAR(50) DEFAULT 'IntraSend-MPesa',
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO payments (user_id, amount, payment_method, status) VALUES
(1, 50.00, 'IntraSend-MPesa', 'SUCCESS'),
(2, 100.00, 'IntraSend-MPesa', 'PENDING'),
(3, 75.00, 'IntraSend-MPesa', 'SUCCESS');