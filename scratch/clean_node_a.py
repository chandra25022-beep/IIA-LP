import requests

url_a = "https://mooned-antics-shorter.ngrok-free.dev"
headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}

q1 = "DELETE FROM vehicle_registration WHERE vehicle_reg_no = 'KA51VIVA2026'"
q2 = "DELETE FROM insurance_records WHERE registration_id = 'KA51VIVA2026'"

r1 = requests.post(f"{url_a}/api/node/sql-write", headers=headers, json={"database": "registration", "query": q1}, timeout=10)
r2 = requests.post(f"{url_a}/api/node/sql-write", headers=headers, json={"database": "insurance", "query": q2}, timeout=10)
print("Cleaned from Node A:", r1.json(), r2.json())
