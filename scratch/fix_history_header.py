import os

path = r'C:\Major Project Using MERN Stack\AcadFusion Ai\templates\history.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Desired new header
new_header = """        <div class="header">
            <a href="/hub" class="brand-header">
                <img src="{{ url_for('static', filename='img/logo.png') }}" alt="AcadFusion AI" class="brand-logo">
                <div class="brand-info">
                    <span class="brand-name">History Hub</span>
                    <span class="brand-tagline">Centralized System Records</span>
                </div>
            </a>
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Light/Dark Mode">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                </button>
                <div class="user-badge" style="display: flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.05); padding: 0.4rem 1rem; border-radius: 99px; border: 1px solid var(--glass-border); font-size: 0.8rem; color: var(--text-secondary);">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    Logged in as: {{ session.get('user_name', 'Faculty') }}
                </div>
                <a href="{{ url_for('auth.logout') }}" class="logout" style="color: #ef4444; font-weight: 700; text-decoration: none; font-size: 0.85rem;">Logout</a>
            </div>
        </div>"""

# Find the header block
import re
# Match <div class="header"> ... </div> (including the closing div of gadgets)
# We know the specific structure from view_file
pattern = r'        <div class="header">.*?        </div>\s+</div>'
# Wait, the structure is:
# <div class="header">
#   <a ...></a>
#   <div class="header-gadgets"> ... </div>
# </div>

pattern = re.compile(r'        <div class="header">.*?        </div>\s+</div>', re.DOTALL)
new_content = pattern.sub(new_header, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replacement complete.")
