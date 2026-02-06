import sqlite3

conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, tech_stack, price, rating FROM products WHERE status="PUBLISHED" LIMIT 10')

print("=" * 80)
print("数据库中的商品数据")
print("=" * 80)

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"技术栈: {row[2]}")
    print(f"价格: ¥{row[3]}")
    print(f"评分: {row[4]}⭐")
    print("-" * 80)

conn.close()
