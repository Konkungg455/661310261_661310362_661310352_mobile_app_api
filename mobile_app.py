import flet as ft
import requests
import random
from datetime import datetime, timedelta

# ปรับ URL ให้ตรงกับ FastAPI ของคุณ
BASE_URL = "http://192.168.1.40:3000/"
ROOMS_URL = f"{BASE_URL}/rooms"
LOGIN_URL = f"{BASE_URL}/login"
BOOKING_URL = f"{BASE_URL}/bookings"
REGISTER_URL = f"{BASE_URL}/users" 

def main(page: ft.Page):
    page.title = "Tutor Room Booking System"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"
    page.scroll = "auto"

    current_user = None
    room_list_container = ft.Column(spacing=10)

    # ---------------------
    # LOGOUT ACTION
    # ---------------------
    def logout_action(e):
        nonlocal current_user
        current_user = None 
        page.controls.clear()
        page.appbar = None 
        page.drawer = None 
        build_login() 
        page.update()

    # ---------------------
    # BOOKING LOGIC
    # ---------------------
    def send_booking_request(room_id):
        if not current_user: return
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2)
        payload = {
            "user_id": current_user["user_id"],
            "room_id": room_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        try:
            r = requests.post(BOOKING_URL, json=payload)
            if r.status_code == 200:
                page.snack_bar = ft.SnackBar(ft.Text("จองห้องสำเร็จแล้ว!"), bgcolor="green")
                page.snack_bar.open = True
                build_home()
            else:
                msg = r.json().get("detail", "จองไม่สำเร็จ")
                page.snack_bar = ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red")
                page.snack_bar.open = True
        except:
            page.snack_bar = ft.SnackBar(ft.Text("เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    # ---------------------------------------------------------
    # SHOW ID PAGE (หน้าใหม่ที่จะเด้งไปหลังสมัครเสร็จ)
    # ---------------------------------------------------------
    def build_show_id(generated_sid):
        page.controls.clear()
        page.add(
            ft.Container(
                expand=True,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="green", size=100),
                        ft.Text("สมัครสมาชิกสำเร็จ!", size=32, weight="bold"),
                        ft.Container(height=10),
                        ft.Text("Student ID ของคุณคือ:", size=20),
                        ft.Container(
                            content=ft.Text(generated_sid, size=48, weight="bold", color="blue"),
                            bgcolor="#1E1E1E",
                            padding=20,
                            border_radius=15,
                            border=ft.border.all(2, "blue")
                        ),
                        ft.Text("กรุณาจดจำรหัสนี้เพื่อใช้ในการเข้าสู่ระบบ", color="grey"),
                        ft.Container(height=30),
                        ft.FilledButton(
                            "กลับไปยังหน้า Login", 
                            width=300, 
                            height=50,
                            on_click=lambda _: (page.controls.clear(), build_login(), page.update())
                        )
                    ]
                )
            )
        )
        page.update()

    # ---------------------
    # REGISTER PROCESS
    # ---------------------
    def register_process(e):
        name = reg_name_field.value
        pw = reg_pw_field.value
        if not name or not pw:
            reg_error.value = "กรุณากรอกข้อมูลให้ครบถ้วนนะจ๊ะ"
            page.update()
            return

        random_suffix = "".join([str(random.randint(0, 9)) for _ in range(4)])
        generated_sid = f"640{random_suffix}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        payload = {
            "full_name": name, 
            "student_id": generated_sid, 
            "password": pw,
            "created_at": created_at
        }
        try:
            r = requests.post(REGISTER_URL, json=payload)
            if r.status_code == 200 or r.status_code == 201:
                # สมัครเสร็จ ดีดไปหน้าโชว์รหัสทันที!
                build_show_id(generated_sid)
            else:
                reg_error.value = "สมัครไม่สำเร็จ: " + str(r.json().get("detail"))
                page.update()
        except:
            reg_error.value = "ติดต่อ Server ไม่ได้จ้า"
            page.update()

    # ---------------------
    # LOGIN PROCESS
    # ---------------------
    def login_process(e):
        nonlocal current_user
        student_id = student_id_field.value
        password = password_field.value
        error_text.value = "" 

        if not student_id or not password:
            error_text.value = "กรุณากรอกข้อมูลให้ครบถ้วนครับ"
            page.update()
            return

        try:
            r = requests.post(LOGIN_URL, json={"student_id": student_id, "password": password})
            if r.status_code == 200:
                res_data = r.json()
                current_user = res_data.get("user")
                page.controls.clear()
                if student_id == "admin":
                    build_admin_dashboard()
                else:
                    build_home()
                page.update()
            else:
                error_text.value = "Student ID หรือรหัสผ่านไม่ถูกต้อง"
                page.update()
        except Exception as ex:
            error_text.value = f"เชื่อมต่อ Server ไม่ได้: {ex}"
            page.update()

    def build_login():
        global student_id_field, password_field, error_text
        page.bgcolor = "#121212"
        page.appbar = None
        page.drawer = None
        student_id_field = ft.TextField(label="Student ID", border="underline", width=300)
        password_field = ft.TextField(label="Password", border="underline", password=True, can_reveal_password=True, width=300)
        error_text = ft.Text("", color="red", size=14)
        
        page.add(
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.LOCK_PERSON, size=80, color="blue"),
                        ft.Text("Tutor Booking", size=32, weight="bold"), 
                        ft.Container(height=20),
                        student_id_field, password_field, error_text,
                        ft.Container(height=10),
                        ft.FilledButton("Login", on_click=login_process, width=300, height=50),
                        ft.TextButton("ยังไม่มีบัญชี? สมัครสมาชิก (Sign Up)", on_click=lambda _: build_register())
                    ]
                ),
                expand=True, alignment=ft.Alignment(0, 0) 
            )
        )

    def build_register():
        global reg_name_field, reg_pw_field, reg_error
        page.controls.clear()
        reg_name_field = ft.TextField(label="ชื่อ-นามสกุล", border="underline", width=300)
        reg_pw_field = ft.TextField(label="กำหนดรหัสผ่าน", border="underline", password=True, can_reveal_password=True, width=300)
        reg_error = ft.Text("", color="red")
        
        page.add(
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.PERSON_ADD, size=80, color="green"),
                        ft.Text("สมัครสมาชิกใหม่", size=32, weight="bold"),
                        ft.Container(height=10),
                        reg_name_field, reg_pw_field, reg_error,
                        ft.Container(height=10),
                        ft.FilledButton("ยืนยันการสมัคร", on_click=register_process, width=300, height=50),
                        ft.TextButton("กลับไปหน้า Login", on_click=lambda _: (page.controls.clear(), build_login(), page.update()))
                    ]
                ),
                expand=True, alignment=ft.Alignment(0, 0)
            )
        )

    # ---------------------
    # ADMIN CRUD DASHBOARD
    # ---------------------
    def delete_room_api(room_id):
        try:
            r = requests.delete(f"{ROOMS_URL}/{room_id}")
            if r.status_code == 200: build_admin_dashboard()
        except: pass

    def build_admin_dashboard():
        page.controls.clear()
        page.bgcolor = "white"
        header_actions = ft.Container(
            padding=20,
            content=ft.Row([
                ft.Text("crud จัดการจองห้อง", size=22, weight="bold", color="black"),
                ft.Row([
                    ft.FilledButton("การเพิ่มห้อง", icon=ft.Icons.ADD, bgcolor=ft.Colors.BLUE, on_click=lambda _: open_admin_editor()),
                    ft.Container(
                        content=ft.TextButton("Logout", on_click=logout_action, style=ft.ButtonStyle(color=ft.Colors.RED)),
                        bgcolor=ft.Colors.BLACK, border_radius=8, padding=ft.padding.symmetric(horizontal=10)
                    )
                ], spacing=10)
            ], alignment="spaceBetween")
        )
        
        table_header = ft.Container(
            padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "#CCCCCC")),
            content=ft.Row([
                ft.Text("#", width=40, color="grey", weight="bold"),
                ft.Text("Name", width=220, color="grey", weight="bold"),
                ft.Text("Description", expand=True, color="grey", weight="bold"),
                ft.Text("Actions", width=220, color="grey", weight="bold", text_align="center"),
            ])
        )

        rows_col = ft.Column(spacing=0)
        try:
            r = requests.get(ROOMS_URL)
            if r.status_code == 200:
                for idx, room in enumerate(r.json()):
                    rows_col.controls.append(
                        ft.Container(
                            padding=10, border=ft.border.only(bottom=ft.border.BorderSide(0.5, "#EEEEEE")),
                            content=ft.Row([
                                ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, width=40, size=16, color="black"),
                                ft.Text(room["room_name"], width=220, color="black"),
                                ft.Text(room["location"], expand=True, color="black"),
                                ft.Row([
                                    ft.FilledButton("Delete", bgcolor="#D9534F", on_click=lambda _, rid=room["room_id"]: delete_room_api(rid)),
                                    ft.FilledButton("Edit", bgcolor="#5CB85C", on_click=lambda _, r=room: open_admin_editor(r)),
                                ], spacing=5)
                            ])
                        )
                    )
        except: pass
        page.add(ft.Column([header_actions, table_header, rows_col]))
        page.update()

    def open_admin_editor(room=None):
        page.controls.clear()
        page.bgcolor = "#F4F4F4"
        title = "แก้ไขข้อมูลห้อง" if room else "การเพิ่มห้อง"
        name_f = ft.TextField(label="ชื่อห้อง", value=room["room_name"] if room else "", bgcolor="white", color="black")
        cap_f = ft.TextField(label="ความจุ", value=str(room["capacity"]) if room else "", bgcolor="white", color="black")
        loc_f = ft.TextField(label="สถานที่", value=room["location"] if room else "", bgcolor="white", color="black")
        avail_f = ft.Checkbox(label="พร้อมใช้งาน", value=room["is_available"] if room else True, label_style=ft.TextStyle(color="black"))
        page.add(
            ft.Container(padding=30, content=ft.Column([
                ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: build_admin_dashboard(), icon_color="black"), ft.Text(title, size=24, weight="bold", color="black")]),
                name_f, cap_f, loc_f, avail_f,
                ft.FilledButton("บันทึกข้อมูล", icon=ft.Icons.SAVE, bgcolor=ft.Colors.BLUE,
                                 on_click=lambda e: save_room_api(e, room["room_id"] if room else None, name_f, cap_f, loc_f, avail_f))
            ]))
        )
        page.update()

    def save_room_api(e, room_id, name, cap, loc, avail):
        data = {"room_name": name.value, "capacity": int(cap.value), "is_available": avail.value, "location": loc.value}
        try:
            if room_id: requests.put(f"{ROOMS_URL}/{room_id}", json=data)
            else: requests.post(ROOMS_URL, json=data)
            build_admin_dashboard()
        except: pass

    # ---------------------
    # USER HOME
    # ---------------------
    def build_home():
        page.controls.clear()
        page.bgcolor = "#121212"
        page.drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(height=12),
                ft.Container(content=ft.Text("เมนูบริการ", size=20, weight="bold"), padding=20),
                ft.Divider(),
                ft.NavigationDrawerDestination(label="หน้าแรก", icon=ft.Icons.HOME),
                ft.NavigationDrawerDestination(label="ประวัติการจอง", icon=ft.Icons.HISTORY),
            ]
        )
        page.appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.MENU, icon_color="white", on_click=lambda _: page.drawer.open_drawer()),
            title=ft.Text(f"Tutor Booking - {current_user['full_name']}"),
            center_title=True, bgcolor="#1E1E1E",
            actions=[ft.Container(content=ft.TextButton("Logout", on_click=logout_action, style=ft.ButtonStyle(color=ft.Colors.RED)), bgcolor=ft.Colors.BLACK, margin=ft.margin.only(right=10), border_radius=8)]
        )
        room_list_container.controls.clear()
        try:
            r = requests.get(ROOMS_URL)
            if r.status_code == 200:
                for room in r.json():
                    is_avail = room.get("is_available")
                    room_list_container.controls.append(
                        ft.Container(
                            bgcolor="#1E1E1E", border_radius=12, padding=15, ink=True,
                            on_click=lambda e, r=room: open_room_detail(r),
                            content=ft.Row([
                                ft.Icon(ft.Icons.DOOR_FRONT_DOOR, size=40, color="blue" if is_avail else "red"),
                                ft.Column([ft.Text(room["room_name"], weight="bold", size=16), ft.Text(f"ความจุ: {room['capacity']} ท่าน", size=12)], expand=True),
                                ft.Text("ว่าง" if is_avail else "ไม่ว่าง", color="green" if is_avail else "red", weight="bold")
                            ])
                        )
                    )
        except: pass
        page.add(ft.Container(padding=15, content=ft.Column([ft.Text("รายการห้องติว", size=20, weight="bold"), room_list_container])))
        page.update()

    # ---------------------
    # PREMIUM ROOM DETAIL
    # ---------------------
    def open_room_detail(room):
        page.controls.clear()
        status_text = "พร้อมให้จอง" if room.get("is_available") else "กำลังมีการใช้งาน"
        status_color = "green" if room.get("is_available") else "red"
        page.add(
            ft.Container(
                padding=20,
                content=ft.Column(
                    spacing=25,
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda _: build_home(), icon_size=20),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(content=ft.Icon(ft.Icons.MEETING_ROOM_ROUNDED, size=100, color="blue"), bgcolor="#252525", padding=30, border_radius=20),
                                ft.Container(height=10),
                                ft.Text(room.get("room_name", "N/A"), size=36, weight="bold"),
                                ft.Container(content=ft.Text(status_text, color=status_color, size=14, weight="bold"), padding=ft.padding.symmetric(horizontal=12, vertical=4), border=ft.border.all(1, status_color), border_radius=10),
                            ]
                        ),
                        ft.Divider(color="#333333"),
                        ft.Column(
                            spacing=15,
                            controls=[
                                ft.Row([ft.Icon(ft.Icons.LOCATION_ON, color="orange", size=20), ft.Text(f"สถานที่: {room.get('location','ไม่ระบุ')}", size=18)]),
                                ft.Row([ft.Icon(ft.Icons.PEOPLE, color="blue", size=20), ft.Text(f"ความจุสูงสุด: {room.get('capacity','0')} คน", size=18)]),
                                ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color="grey", size=20), ft.Text("คำอธิบายห้อง:", size=16, color="grey")]),
                                ft.Container(content=ft.Text("ห้องติวนี้มาพร้อมกับอุปกรณ์ครบครัน กรุณารักษาความสะอาด", size=14, color="#AAAAAA"), padding=ft.padding.only(left=30))
                            ]
                        ),
                        ft.Container(height=20),
                        ft.FilledButton(
                            content=ft.Row([ft.Icon(ft.Icons.BOOK_ONLINE), ft.Text("ยืนยันการจองห้องนี้ (2 ชั่วโมง)", size=16, weight="bold")], alignment="center"),
                            width=1000, height=60, bgcolor="blue" if room.get("is_available") else "grey",
                            on_click=lambda _: send_booking_request(room["room_id"]) if room.get("is_available") else None,
                            disabled=not room.get("is_available")
                        ),
                    ]
                )
            )
        )
        page.update()

    build_login()

if __name__ == "__main__":
    ft.run(main)