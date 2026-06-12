"""Generates documentation HTML from collected data"""

from typing import Dict, Any, Optional
from pathlib import Path
import json

DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Courier New', monospace;
            background: #000000;
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        .navbar {
            background: #0a0a0a;
            border-bottom: 1px solid #1a1a1a;
            padding: 1rem 2rem;
            font-size: 0.85rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar a {
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }
        
        .navbar a:hover {
            border-bottom-color: #fff;
        }
        
        .container {
            display: flex;
            min-height: calc(100vh - 60px);
        }
        
        .sidebar {
            width: 280px;
            background: #0a0a0a;
            border-right: 1px solid #1a1a1a;
            position: fixed;
            height: calc(100vh - 60px);
            overflow-y: auto;
        }
        
        .sidebar-header {
            padding: 1.5rem;
            border-bottom: 1px solid #1a1a1a;
        }
        
        .sidebar-header h2 {
            font-size: 1.2rem;
            margin-bottom: 0.25rem;
            color: #ffffff;
        }
        
        .version {
            font-size: 0.7rem;
            color: #ff4444;
        }
        
        .sidebar-nav {
            padding: 1rem 0;
            border-bottom: 1px solid #1a1a1a;
        }
        
        .nav-item {
            padding: 0.6rem 1.5rem;
            cursor: pointer;
            transition: all 0.2s;
            color: #aaa;
            font-size: 0.85rem;
        }
        
        .nav-item:hover {
            background: #1a1a1a;
            color: #ffffff;
        }
        
        .nav-item.active {
            background: #1a1a1a;
            color: #ff4444;
            border-right: 2px solid #ff4444;
        }
        
        .sidebar-groups {
            padding: 1rem 1.5rem;
        }
        
        .sidebar-groups h3 {
            font-size: 0.7rem;
            text-transform: uppercase;
            color: #555;
            margin-bottom: 1rem;
            letter-spacing: 1px;
        }
        
        .group-item {
            margin-bottom: 1rem;
        }
        
        .group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: #0a0a0a;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .group-header:hover {
            background: #1a1a1a;
        }
        
        .group-name {
            color: #ffb86b;
        }
        
        .group-count {
            background: #1a1a1a;
            padding: 0.1rem 0.4rem;
            border-radius: 10px;
            font-size: 0.7rem;
            color: #aaa;
        }
        
        .group-routes {
            padding-left: 1rem;
            margin-top: 0.5rem;
            display: none;
        }
        
        .group-item.active .group-routes {
            display: block;
        }
        
        .group-route {
            padding: 0.3rem 0;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .method-mini {
            font-size: 0.65rem;
            padding: 0.1rem 0.3rem;
            font-weight: bold;
        }
        
        .content {
            flex: 1;
            margin-left: 280px;
            padding: 2rem;
        }
        
        .content-header {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #1a1a1a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .content-header h1 {
            font-size: 1.5rem;
            color: #ffffff;
        }
        
        .search-box input {
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 0.5rem 1rem;
            color: #e0e0e0;
            font-family: monospace;
            font-size: 0.85rem;
            width: 250px;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #ff4444;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1.5rem;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #ff4444;
        }
        
        .stat-label {
            color: #666;
            margin-top: 0.5rem;
            font-size: 0.8rem;
        }
        
        .route-card {
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        .route-header {
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            cursor: pointer;
            transition: background 0.2s;
            flex-wrap: wrap;
        }
        
        .route-header:hover {
            background: #1a1a1a;
        }
        
        .method-badge {
            padding: 0.2rem 0.6rem;
            font-weight: bold;
            font-size: 0.7rem;
            letter-spacing: 1px;
        }
        
        .method-GET { background: #0a4d4d; color: #4ec9b0; border: 1px solid #4ec9b0; }
        .method-POST { background: #4d3a0a; color: #fca130; border: 1px solid #fca130; }
        .method-PUT { background: #0a2d4d; color: #61affe; border: 1px solid #61affe; }
        .method-DELETE { background: #4d0a0a; color: #f93e3e; border: 1px solid #f93e3e; }
        .method-PATCH { background: #0a4d2d; color: #50e3c2; border: 1px solid #50e3c2; }
        
        .route-path {
            font-family: monospace;
            font-size: 0.9rem;
            color: #ffb86b;
        }
        
        .toggle-btn {
            margin-left: auto;
            background: none;
            border: none;
            cursor: pointer;
            color: #555;
            font-size: 1rem;
        }
        
        .toggle-btn:hover {
            color: #fff;
        }
        
        .route-details {
            padding: 0 1.5rem;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        
        .route-details.open {
            max-height: 600px;
            padding: 0 1.5rem 1.5rem 1.5rem;
        }
        
        .detail-section {
            margin-bottom: 1rem;
        }
        
        .detail-section strong {
            color: #ff4444;
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .params-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        
        .params-table th,
        .params-table td {
            padding: 0.5rem;
            text-align: left;
            border-bottom: 1px solid #1a1a1a;
        }
        
        .params-table th {
            background: #1a1a1a;
            color: #ffb86b;
        }
        
        .method-bar {
            margin-bottom: 1rem;
        }
        
        .method-bar-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            font-size: 0.8rem;
        }
        
        .method-bar-bg {
            background: #1a1a1a;
            height: 4px;
            overflow: hidden;
        }
        
        .method-bar-fill {
            height: 100%;
            transition: width 0.5s;
        }
        
        code {
            background: #1a1a1a;
            padding: 0.2rem 0.4rem;
            font-family: monospace;
            font-size: 0.8rem;
            color: #ffb86b;
        }
        
        .file-path {
            color: #4ec9b0;
            font-size: 0.75rem;
        }
        
        .signature {
            display: block;
            background: #1a1a1a;
            padding: 0.5rem;
            overflow-x: auto;
            font-size: 0.75rem;
        }
        
        ::selection {
            background: #ff4444;
            color: #000000;
        }
        
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            .content {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <span style="color: #ff4444;">FASTAPI ROUTE</span>
        <span style="color: #333;"> | </span>
        <a href="/">HOME</a>
        <span style="color: #333;"> | </span>
        <a href="/docs">DOCS</a>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>{{project_name}}</h2>
                <span class="version">v{{version}}</span>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item active" data-section="overview">OVERVIEW</div>
                <div class="nav-item" data-section="routes">ROUTES</div>
                <div class="nav-item" data-section="statistics">STATISTICS</div>
            </div>
            <div class="sidebar-groups">
                <h3>ROUTE GROUPS</h3>
                <div class="groups-list"></div>
            </div>
        </div>
        
        <div class="content">
            <div class="content-header">
                <h1>API Documentation</h1>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="[ SEARCH ROUTES ]">
                </div>
            </div>
            
            <div id="overview-section" class="section">
                <div class="stats-grid"></div>
                <div class="methods-stats">
                    <h3 style="margin-bottom: 1rem; font-size: 0.9rem; letter-spacing: 1px;">HTTP METHODS</h3>
                    <div class="method-bars"></div>
                </div>
            </div>
            
            <div id="routes-section" class="section" style="display: none;">
                <div class="routes-list"></div>
            </div>
            
            <div id="statistics-section" class="section" style="display: none;">
                <div class="detailed-stats"></div>
            </div>
        </div>
    </div>
    
    <script>
        const routesData = {{routes}};
        const groupsData = {{groups}};
        const statisticsData = {{statistics}};
        
        function renderStats() {
            const container = document.querySelector('.stats-grid');
            const stats = statisticsData;
            container.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${stats.total_routes}</div>
                    <div class="stat-label">TOTAL ROUTES</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.dynamic_routes}</div>
                    <div class="stat-label">DYNAMIC</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.static_routes}</div>
                    <div class="stat-label">STATIC</div>
                </div>
            `;
        }
        
        function getMethodColor(method) {
            const colors = {
                'GET': '#4ec9b0',
                'POST': '#fca130',
                'PUT': '#61affe',
                'DELETE': '#f93e3e',
                'PATCH': '#50e3c2'
            };
            return colors[method] || '#858585';
        }
        
        function renderMethodStats() {
            const container = document.querySelector('.method-bars');
            const methods = statisticsData.methods;
            const total = Object.values(methods).reduce((a, b) => a + b, 0);
            
            container.innerHTML = Object.entries(methods).map(([method, count]) => {
                const percentage = (count / total) * 100;
                return `
                    <div class="method-bar">
                        <div class="method-bar-label">
                            <span style="color: ${getMethodColor(method)}">${method}</span>
                            <span>${count} (${percentage.toFixed(1)}%)</span>
                        </div>
                        <div class="method-bar-bg">
                            <div class="method-bar-fill" style="width: ${percentage}%; background-color: ${getMethodColor(method)}"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function renderRoutes() {
            const container = document.querySelector('.routes-list');
            container.innerHTML = routesData.map(route => `
                <div class="route-card" data-path="${route.path}" data-method="${route.method}">
                    <div class="route-header">
                        <span class="method-badge method-${route.method}">${route.method}</span>
                        <span class="route-path">${route.path}</span>
                        <button class="toggle-btn">▼</button>
                    </div>
                    <div class="route-details">
                        <div class="detail-section">
                            <strong>DESCRIPTION</strong>
                            <p style="font-size: 0.85rem;">${route.docstring || 'No description available'}</p>
                        </div>
                        ${route.parameters && route.parameters.length > 0 ? `
                            <div class="detail-section">
                                <strong>PARAMETERS</strong>
                                <table class="params-table">
                                    <tr><th>NAME</th><th>TYPE</th><th>REQUIRED</th><th>DESCRIPTION</th></tr>
                                    ${route.parameters.map(p => `
                                        <tr>
                                            <td><code>${p.name}</code></td>
                                            <td>${p.type}</td>
                                            <td>${p.required ? 'YES' : 'NO'}</td>
                                            <td>${p.description || '-'}</td>
                                        </tr>
                                    `).join('')}
                                </table>
                            </div>
                        ` : ''}
                        <div class="detail-section">
                            <strong>SOURCE</strong>
                            <code class="file-path">${route.file_path}</code>
                        </div>
                        <div class="detail-section">
                            <strong>SIGNATURE</strong>
                            <code class="signature">${route.signature}</code>
                        </div>
                    </div>
                </div>
            `).join('');
            
            document.querySelectorAll('.route-card').forEach(card => {
                const btn = card.querySelector('.toggle-btn');
                const details = card.querySelector('.route-details');
                btn.addEventListener('click', () => {
                    details.classList.toggle('open');
                    btn.textContent = details.classList.contains('open') ? '▲' : '▼';
                });
            });
        }
        
        function renderGroups() {
            const container = document.querySelector('.groups-list');
            container.innerHTML = Object.entries(groupsData).map(([group, routes]) => `
                <div class="group-item">
                    <div class="group-header">
                        <span class="group-name">${group}</span>
                        <span class="group-count">${routes.length}</span>
                    </div>
                    <div class="group-routes">
                        ${routes.map(r => `
                            <div class="group-route">
                                <span class="method-mini" style="color: ${getMethodColor(r.method)}">${r.method}</span>
                                <span style="color: #888;">${r.path}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
            document.querySelectorAll('.group-header').forEach(header => {
                header.addEventListener('click', () => {
                    header.parentElement.classList.toggle('active');
                });
            });
        }
        
        function setupNavigation() {
            const sections = {
                overview: document.getElementById('overview-section'),
                routes: document.getElementById('routes-section'),
                statistics: document.getElementById('statistics-section')
            };
            
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', () => {
                    const section = item.dataset.section;
                    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                    item.classList.add('active');
                    Object.values(sections).forEach(s => s.style.display = 'none');
                    sections[section].style.display = 'block';
                });
            });
        }
        
        function filterRoutes() {
            const term = document.getElementById('search-input').value.toLowerCase();
            document.querySelectorAll('.route-card').forEach(card => {
                const path = card.dataset.path.toLowerCase();
                const method = card.dataset.method.toLowerCase();
                const matches = path.includes(term) || method.includes(term);
                card.style.display = matches ? '' : 'none';
            });
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            renderStats();
            renderMethodStats();
            renderRoutes();
            renderGroups();
            setupNavigation();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.addEventListener('input', filterRoutes);
            }
        });
    </script>
</body>
</html>
"""

class DocsGenerator:
    """Generates HTML documentation"""
    
    def __init__(self, docs_data: Dict[str, Any], custom_template: Optional[str] = None):
        self.docs_data = docs_data
        self.custom_template = custom_template
    
    def generate_html(self) -> str:
        """Generate HTML documentation"""
        template = self.custom_template if self.custom_template else DEFAULT_TEMPLATE
        
        context = {
            "title": f"{self.docs_data['info']['name']} - API Documentation",
            "project_name": self.docs_data['info']['name'],
            "version": self.docs_data['info']['version'],
            "routes": json.dumps(self.docs_data['routes'], indent=2),
            "groups": json.dumps(self.docs_data['groups'], indent=2),
            "statistics": json.dumps(self.docs_data['statistics'], indent=2),
            "info": self.docs_data['info'],
        }
        
        html = template
        for key, value in context.items():
            html = html.replace(f"{{{{{key}}}}}", str(value))
        
        return html
    
    def save_to_file(self, output_path: Path) -> None:
        """Save documentation to HTML file"""
        html = self.generate_html()
        output_path.write_text(html, encoding='utf-8')