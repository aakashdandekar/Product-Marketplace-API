db.products.dropIndexes()
db.products.createIndex({ caption: "text", product_type: "text" })