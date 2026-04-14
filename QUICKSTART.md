# UAP SmartCampus - Quick Start Guide

## 🌐 Portal URLs

### User Portal
- **Login**: http://127.0.0.1:8001/login/
- **Dashboard**: http://127.0.0.1:8001/dashboard/
- **Cafeteria**: http://127.0.0.1:8001/cafeteria/
- **Transportation**: http://127.0.0.1:8001/transportation/
- **Events & Clubs**: http://127.0.0.1:8001/events/
- **SmartCampus AI**: http://127.0.0.1:8001/ai/

### Authority Management Portal (Admin)
- **Authority Login**: http://127.0.0.1:8001/authority/login/
- **Authority Dashboard**: http://127.0.0.1:8001/authority/dashboard/
- **Menu Management**: http://127.0.0.1:8001/authority/menu/
- **Add Menu Item**: http://127.0.0.1:8001/authority/menu/add/

### Django Admin (Built-in)
- **Django Admin**: http://127.0.0.1:8001/admin/

---

## 🔐 Access Credentials

To access the **Authority Management Portal**, you need a user with admin/staff privileges.

### Create a Superuser (if you haven't):
```bash
python3 manage.py createsuperuser
```

Then use those credentials to login at `/authority/login/`

---

## 📋 Features

### User Portal
- ✅ Dashboard with quick stats
- ✅ Cafeteria menu viewer (displays available menu items)
- ✅ Sidebar navigation
- ✅ User avatar with logout dropdown
- ✅ Black & white theme with Tailwind CSS

### Authority Management Portal
- ✅ Separate admin login page
- ✅ Dashboard with statistics
- ✅ Add new menu items (name, description, price, category, image)
- ✅ Edit existing menu items
- ✅ Delete menu items
- ✅ Toggle item availability
- ✅ View all menu items in a table
- ✅ Only accessible to admin/staff users

---

## 🍽️ Menu Categories

When adding menu items, you can choose from:
- Breakfast
- Lunch
- Dinner
- Snacks
- Beverages

---

## 🎨 Design

- **Theme**: Black and white color scheme
- **Framework**: Tailwind CSS (via CDN)
- **Icons**: Font Awesome 6.4.0
- **Responsive**: Mobile-friendly design

---

## 📝 Notes

- The Authority Portal is completely separate from Django's built-in `/admin`
- Only users with `is_staff` or `is_superuser` status can access the Authority Portal
- Menu items marked as "unavailable" won't show in the user cafeteria page
- Images are optional for menu items
- All changes in Authority Portal are immediately reflected in the User Portal

---

## 🚀 Running the Server

```bash
source .venv/bin/activate
python3 manage.py runserver 8001
```

The server is currently running on: **http://127.0.0.1:8001**
