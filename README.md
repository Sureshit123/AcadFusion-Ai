# AcadFusion AI

AcadFusion AI is a comprehensive academic management suite designed to streamline departmental operations. It combines advanced data scraping, intelligent scheduling algorithms, and a premium user interface to provide a seamless experience for academic administrators.

## 🚀 Key Modules

### 1. VTU Result Analyzer
- **Automated Scraping**: Fetch results for multiple USNs via sequential auto-generation or bulk file upload.
- **Intelligent Processing**: Automatically extracts student data, SGPA, grades, and subject details.
- **Comprehensive Analytics**: Generates a multi-sheet Excel report including:
  - **All Results**: Raw data for every student.
  - **Toppers**: Ranked list of top performers.
  - **Analytics**: Pass/Fail percentages and subject-wise performance.
- **Mock Mode**: Built-in simulator for testing without hitting live VTU servers.

### 2. Departmental Timetable Generator
- **Smart Scheduling**: Generates conflict-free timetables for multiple semesters simultaneously.
- **Modification Workflow**: Re-hydrate past timetables from the History Hub to tweak and regenerate without starting over.
- **Pedagogical Constraints**: Strictly enforces a "one class per subject per day" rule for better academic distribution.
- **Resource Management**: Tracks teacher availability and physical lab room constraints to prevent double-booking.
- **Constraint-Aware**: Automatically handles Saturday variations, session breaks, and parallel batch lab sessions.
- **Holiday Reasons**: Add custom justifications for Saturday holidays, displayed in bold on the grid.
- **Export to Excel**: One-click generation of professional timetable spreadsheets.

### 3. Secure Admin Panel
- **Authentication**: Secure login system for authorized department personnel.
- **Dynamic Configuration**: Easily configure teacher pools, lab rooms, and semester subjects.

## 🎨 Design Aesthetics
- **Premium UI**: Modern dark-themed interface with glassmorphism effects.
- **Responsive Layout**: Works seamlessly across desktops, tablets, and mobile devices.
- **Real-time Feedback**: Dynamic progress bars and live status updates during processing tasks.

---

## 🛠️ Technology Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+)
- **Data Processing**: Pandas, OpenPyXL, BeautifulSoup4
- **Database**: MongoDB (with Atlas support)
- **Environment**: Decoupled configuration via `.env`

---

## ⚙️ Local Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Sureshit123/AcadFusion-Ai.git
   cd AcadFusion-Ai
   ```

2. **Setup a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   FLASK_SECRET_KEY=your_secret_key
   MONGO_URI=your_mongodb_atlas_uri
   ADMIN_PASSWORD=admin123
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   Access the app at `http://localhost:5000`.

---

## 🚀 Deployment

Designed to be easily deployed on **Render**, **Railway**, or **Vercel**.

### Render.com Guide
1. Connect project GitHub repository.
2. Select **Web Service**.
3. **Environment**: Python 3.
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `gunicorn app:app` (The project includes a `Procfile` for auto-detection).
6. **Config**: Add your `.env` variables (e.g., `MONGO_URI`) in the Dashboard.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

Developed with ❤️ for Academic Excellence.
I