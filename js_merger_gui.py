#!/usr/bin/env python3
"""
Interface Tkinter pour JavaScript Code Merger
Interface graphique pour fusionner intelligemment du code JavaScript
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import threading

# Import du code original (adapté pour l'interface)
@dataclass
class JSFunction:
    """Représente une fonction JavaScript"""
    name: str
    full_code: str
    start_line: int
    end_line: int
    is_arrow_function: bool = False
    is_method: bool = False
    signature: str = ""
    comments: str = ""

class JavaScriptMerger:
    """Fusioneur intelligent de code JavaScript"""
    
    def __init__(self, backup_enabled: bool = True, callback=None):
        self.backup_enabled = backup_enabled
        self.callback = callback  # Pour les messages vers l'interface
        self.function_patterns = {
            'classic': r'function\s+(\w+)\s*\([^)]*\)\s*{',
            'arrow_const': r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{',
            'arrow_let': r'let\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{',
            'method': r'(\w+)\s*[:=]\s*function\s*\([^)]*\)\s*{|(\w+)\s*\([^)]*\)\s*{',
        }
        
    def log_message(self, message: str):
        """Envoie un message à l'interface si callback disponible"""
        if self.callback:
            self.callback(message)
        else:
            print(message)
    
    def create_backup(self, file_path: str) -> str:
        """Crée une sauvegarde du fichier original"""
        if not self.backup_enabled:
            return ""
            
        backup_name = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_name, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        return backup_name
    
    def extract_functions(self, js_code: str) -> Dict[str, JSFunction]:
        """Extrait toutes les fonctions du code JavaScript"""
        functions = {}
        lines = js_code.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line.startswith('//') or line.startswith('/*'):
                i += 1
                continue
            
            func_match = self._find_function_start(line)
            if func_match:
                func_name, func_type = func_match
                func_info = self._extract_complete_function(lines, i, func_name, func_type)
                if func_info:
                    functions[func_name] = func_info
                    i = func_info.end_line
                else:
                    i += 1
            else:
                i += 1
                
        return functions
    
    def _find_function_start(self, line: str) -> Optional[Tuple[str, str]]:
        """Trouve le début d'une fonction et retourne (nom, type)"""
        for pattern_type, pattern in self.function_patterns.items():
            match = re.search(pattern, line)
            if match:
                if pattern_type == 'method':
                    func_name = match.group(1) or match.group(2)
                else:
                    func_name = match.group(1)
                return (func_name, pattern_type)
        return None
    
    def _extract_complete_function(self, lines: List[str], start_idx: int, 
                                 func_name: str, func_type: str) -> Optional[JSFunction]:
        """Extrait une fonction complète avec gestion des accolades imbriquées"""
        brace_count = 0
        started = False
        end_idx = start_idx
        func_lines = []
        
        comment_lines = []
        comment_idx = start_idx - 1
        while comment_idx >= 0:
            line = lines[comment_idx].strip()
            if line.startswith('//') or line.startswith('/*') or '*' in line:
                comment_lines.insert(0, lines[comment_idx])
                comment_idx -= 1
            elif not line:
                comment_idx -= 1
            else:
                break
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            func_lines.append(line)
            
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1
                    
            if started and brace_count == 0:
                end_idx = i
                break
        
        if not started or brace_count != 0:
            return None
            
        signature = lines[start_idx].strip()
        
        return JSFunction(
            name=func_name,
            full_code='\n'.join(func_lines),
            start_line=start_idx,
            end_line=end_idx,
            is_arrow_function='arrow' in func_type,
            is_method=func_type == 'method',
            signature=signature,
            comments='\n'.join(comment_lines)
        )
    
    def merge_functions(self, existing_code: str, new_functions_code: str, 
                       strategy: str = 'smart') -> Tuple[str, Dict]:
        """Fusionne les nouvelles fonctions avec le code existant"""
        existing_functions = self.extract_functions(existing_code)
        new_functions = self.extract_functions(new_functions_code)
        
        merge_report = {
            'replaced': [],
            'added': [],
            'conflicts': [],
            'skipped': []
        }
        
        result_lines = existing_code.split('\n')
        
        for func_name, new_func in new_functions.items():
            if func_name in existing_functions:
                existing_func = existing_functions[func_name]
                
                if strategy == 'smart':
                    action = self._decide_merge_action(existing_func, new_func)
                elif strategy == 'replace':
                    action = 'replace'
                else:
                    action = 'skip'
                    
                if action == 'replace':
                    result_lines = self._replace_function(result_lines, existing_func, new_func)
                    merge_report['replaced'].append(func_name)
                elif action == 'conflict':
                    merge_report['conflicts'].append(func_name)
                else:
                    merge_report['skipped'].append(func_name)
            else:
                result_lines = self._add_new_function(result_lines, new_func)
                merge_report['added'].append(func_name)
        
        return '\n'.join(result_lines), merge_report
    
    def _decide_merge_action(self, existing: JSFunction, new: JSFunction) -> str:
        """Décide intelligemment de l'action à prendre"""
        existing_size = len(existing.full_code)
        new_size = len(new.full_code)
        
        if new_size > existing_size * 1.5:
            return 'replace'
            
        if existing.signature.strip() != new.signature.strip():
            return 'replace'
            
        improvement_keywords = ['enhanced', 'improved', 'optimized', 'fixed', 'better']
        if any(keyword in new.comments.lower() for keyword in improvement_keywords):
            return 'replace'
            
        return 'conflict'
    
    def _replace_function(self, lines: List[str], existing: JSFunction, 
                         new: JSFunction) -> List[str]:
        """Remplace une fonction existante par une nouvelle"""
        final_comments = new.comments if new.comments else existing.comments
        
        replacement_lines = []
        if final_comments:
            replacement_lines.extend(final_comments.split('\n'))
        replacement_lines.extend(new.full_code.split('\n'))
        
        return (lines[:existing.start_line] + 
                replacement_lines + 
                lines[existing.end_line + 1:])
    
    def _add_new_function(self, lines: List[str], new_func: JSFunction) -> List[str]:
        """Ajoute une nouvelle fonction à la fin de la section appropriée"""
        insert_position = self._find_best_insert_position(lines, new_func)
        
        new_lines = []
        if new_func.comments:
            new_lines.extend(new_func.comments.split('\n'))
        new_lines.extend(new_func.full_code.split('\n'))
        new_lines.append('')
        
        return lines[:insert_position] + new_lines + lines[insert_position:]
    
    def _find_best_insert_position(self, lines: List[str], new_func: JSFunction) -> int:
        """Trouve la meilleure position pour insérer une nouvelle fonction"""
        section_keywords = {
            'connection': ['connection', 'link', 'relationship'],
            'node': ['node', 'element', 'item'],
            'ui': ['ui', 'interface', 'display', 'show'],
            'utility': ['utility', 'helper', 'tool', 'misc']
        }
        
        # Analyser le nom de la fonction et les commentaires (plus pertinent)
        analysis_text = f"{new_func.name.lower()} {new_func.comments.lower() if new_func.comments else ''}"
        best_section = 'utility'
        
        # Utiliser des recherches de chaînes simples au lieu de regex
        for section, keywords in section_keywords.items():
            if any(keyword in analysis_text for keyword in keywords):
                best_section = section
                break
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if (f'--- {best_section}' in line_lower or 
                f'// {best_section}' in line_lower):
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('// ---') or lines[j].strip().startswith('function'):
                        return j
        
        for i in range(len(lines) - 1, -1, -1):
            if '</script>' in lines[i]:
                return i
            elif 'initialize();' in lines[i]:
                return i
        
        return len(lines)

class JSMergerGUI:
    """Interface graphique pour le fusionneur JavaScript"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JavaScript Code Merger - Fusionneur Intelligent")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Variables
        self.html_file_path = tk.StringVar()
        self.js_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.strategy = tk.StringVar(value="smart")
        self.backup_enabled = tk.BooleanVar(value=True)
        
        # Créer l'interface
        self.create_widgets()
        self.create_menu()
        
        # Style
        self.setup_style()
        
    def setup_style(self):
        """Configure le style de l'interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs personnalisées
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Info.TLabel', foreground='blue')
        
    def create_menu(self):
        """Crée la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau projet", command=self.new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
        help_menu.add_command(label="Guide d'utilisation", command=self.show_help)
    
    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(main_frame, text="JavaScript Code Merger", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Notebook pour organiser les sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet 1: Configuration des fichiers
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_section(config_frame)
        
        # Onglet 2: Code JavaScript à fusionner
        js_frame = ttk.Frame(notebook)
        notebook.add(js_frame, text="Code JavaScript")
        self.create_js_section(js_frame)
        
        # Onglet 3: Résultats et logs
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Résultats")
        self.create_results_section(results_frame)
        
        # Boutons d'action
        self.create_action_buttons(main_frame)
    
    def create_config_section(self, parent):
        """Crée la section de configuration des fichiers"""
        # Fichier HTML source
        html_frame = ttk.LabelFrame(parent, text="Fichier HTML Source", padding=10)
        html_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(html_frame, textvariable=self.html_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(html_frame, text="Parcourir...", command=self.select_html_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Fichier JS ou zone de texte
        js_source_frame = ttk.LabelFrame(parent, text="Source des nouvelles fonctions", padding=10)
        js_source_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.js_source_type = tk.StringVar(value="text")
        ttk.Radiobutton(js_source_frame, text="Saisie directe", variable=self.js_source_type, 
                       value="text", command=self.toggle_js_source).pack(side=tk.LEFT)
        ttk.Radiobutton(js_source_frame, text="Fichier JS", variable=self.js_source_type, 
                       value="file", command=self.toggle_js_source).pack(side=tk.LEFT, padx=(20, 0))
        
        # Frame pour le fichier JS
        self.js_file_frame = ttk.Frame(js_source_frame)
        self.js_file_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Entry(self.js_file_frame, textvariable=self.js_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.js_file_frame, text="Parcourir...", command=self.select_js_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Fichier de sortie
        output_frame = ttk.LabelFrame(parent, text="Fichier de sortie (optionnel)", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(output_frame, textvariable=self.output_file_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Parcourir...", command=self.select_output_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Options
        options_frame = ttk.LabelFrame(parent, text="Options de fusion", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Stratégie
        strategy_frame = ttk.Frame(options_frame)
        strategy_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(strategy_frame, text="Stratégie:").pack(side=tk.LEFT)
        
        strategies = [("Intelligente", "smart"), ("Remplacer", "replace"), ("Ajouter seulement", "add_only")]
        for i, (text, value) in enumerate(strategies):
            ttk.Radiobutton(strategy_frame, text=text, variable=self.strategy, 
                           value=value).pack(side=tk.LEFT, padx=(10 if i > 0 else 20, 0))
        
        # Sauvegarde
        ttk.Checkbutton(options_frame, text="Créer une sauvegarde automatique", 
                       variable=self.backup_enabled).pack(anchor=tk.W)
        
        self.toggle_js_source()  # Initialiser l'état
    
    def create_js_section(self, parent):
        """Crée la section pour saisir le code JavaScript"""
        # Instructions
        instructions = ttk.Label(parent, text="Saisissez ou collez ici les nouvelles fonctions JavaScript à fusionner:")
        instructions.pack(anchor=tk.W, pady=(0, 10))
        
        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.js_text = scrolledtext.ScrolledText(text_frame, height=20, font=('Consolas', 10))
        self.js_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons pour le texte
        text_buttons_frame = ttk.Frame(parent)
        text_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(text_buttons_frame, text="Charger depuis un fichier", 
                  command=self.load_js_from_file).pack(side=tk.LEFT)
        ttk.Button(text_buttons_frame, text="Sauvegarder le code", 
                  command=self.save_js_to_file).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(text_buttons_frame, text="Effacer", 
                  command=self.clear_js_text).pack(side=tk.RIGHT)
        
        # Exemple de code
        example_code = '''// Exemple de nouvelles fonctions à fusionner

function addConnectionsBetweenNodes(nodeNames) {
    const nodesOnCanvas = new Set(nodeNames.filter(name => nameToNodeIdMap.has(name)));
    
    // Ajouter les connexions d'héritage
    relationshipData.inheritance.forEach(rel => {
        if (nodesOnCanvas.has(rel.child) && nodesOnCanvas.has(rel.parent)) {
            addSingleConnection(rel.child, rel.parent, 'output_1', 'input_1', 'inheritance');
        }
    });
}

function forceRefreshAllConnections() {
    editor.clearConnections();
    const allNodesOnCanvas = Array.from(nameToNodeIdMap.keys());
    addConnectionsBetweenNodes(allNodesOnCanvas);
    showMessage('Toutes les connexions ont été rafraîchies', 'info');
}'''
        self.js_text.insert(tk.END, example_code)
    
    def create_results_section(self, parent):
        """Crée la section des résultats et logs"""
        # Zone de résultats
        results_label = ttk.Label(parent, text="Logs et résultats de la fusion:")
        results_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.results_text = scrolledtext.ScrolledText(parent, height=15, font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons pour les résultats
        results_buttons_frame = ttk.Frame(parent)
        results_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(results_buttons_frame, text="Effacer les logs", 
                  command=self.clear_results).pack(side=tk.LEFT)
        ttk.Button(results_buttons_frame, text="Sauvegarder les logs", 
                  command=self.save_results).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_action_buttons(self, parent):
        """Crée les boutons d'action principaux"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Bouton principal de fusion
        self.merge_button = ttk.Button(buttons_frame, text="🔄 Fusionner le code", 
                                      command=self.start_merge, style='Accent.TButton')
        self.merge_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Barre de progression
        self.progress = ttk.Progressbar(buttons_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Bouton d'annulation
        self.cancel_button = ttk.Button(buttons_frame, text="Annuler", 
                                       command=self.cancel_operation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT)
    
    def toggle_js_source(self):
        """Bascule entre saisie directe et fichier pour le JS"""
        if self.js_source_type.get() == "file":
            self.js_file_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.js_file_frame.pack_forget()
    
    def select_html_file(self):
        """Sélectionne le fichier HTML source"""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier HTML",
            filetypes=[("Fichiers HTML", "*.html"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.html_file_path.set(filename)
    
    def select_js_file(self):
        """Sélectionne le fichier JavaScript"""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier JavaScript",
            filetypes=[("Fichiers JavaScript", "*.js"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.js_file_path.set(filename)
    
    def select_output_file(self):
        """Sélectionne le fichier de sortie"""
        filename = filedialog.asksaveasfilename(
            title="Fichier de sortie",
            defaultextension=".html",
            filetypes=[("Fichiers HTML", "*.html"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.output_file_path.set(filename)
    
    def load_js_from_file(self):
        """Charge du code JS depuis un fichier"""
        filename = filedialog.askopenfilename(
            title="Charger du code JavaScript",
            filetypes=[("Fichiers JavaScript", "*.js"), ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.js_text.delete(1.0, tk.END)
                self.js_text.insert(1.0, content)
                self.log_message(f"Code chargé depuis: {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le fichier:\n{e}")
    
    def save_js_to_file(self):
        """Sauvegarde le code JS dans un fichier"""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder le code JavaScript",
            defaultextension=".js",
            filetypes=[("Fichiers JavaScript", "*.js"), ("Fichiers texte", "*.txt")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.js_text.get(1.0, tk.END))
                self.log_message(f"Code sauvegardé dans: {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")
    
    def clear_js_text(self):
        """Efface le contenu de la zone de texte JS"""
        self.js_text.delete(1.0, tk.END)
    
    def clear_results(self):
        """Efface les résultats"""
        self.results_text.delete(1.0, tk.END)
    
    def save_results(self):
        """Sauvegarde les logs"""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder les logs",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.get(1.0, tk.END))
                self.log_message(f"Logs sauvegardés dans: {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")
    
    def log_message(self, message: str, level: str = "info"):
        """Ajoute un message aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.results_text.insert(tk.END, formatted_message)
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_merge(self):
        """Lance la fusion dans un thread séparé"""
        if not self.validate_inputs():
            return
        
        # Désactiver les contrôles
        self.merge_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress.start()
        
        # Lancer dans un thread
        self.merge_thread = threading.Thread(target=self.perform_merge, daemon=True)
        self.merge_thread.start()
    
    def validate_inputs(self) -> bool:
        """Valide les entrées utilisateur"""
        if not self.html_file_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier HTML source.")
            return False
        
        if not os.path.exists(self.html_file_path.get()):
            messagebox.showerror("Erreur", "Le fichier HTML source n'existe pas.")
            return False
        
        # Vérifier la source JavaScript
        if self.js_source_type.get() == "file":
            if not self.js_file_path.get():
                messagebox.showerror("Erreur", "Veuillez sélectionner un fichier JavaScript.")
                return False
            if not os.path.exists(self.js_file_path.get()):
                messagebox.showerror("Erreur", "Le fichier JavaScript n'existe pas.")
                return False
        else:
            if not self.js_text.get(1.0, tk.END).strip():
                messagebox.showerror("Erreur", "Veuillez saisir du code JavaScript à fusionner.")
                return False
        
        return True
    
    def perform_merge(self):
        """Effectue la fusion (appelé dans un thread séparé)"""
        try:
            self.log_message("🚀 Début de la fusion...")
            
            # Créer le merger
            merger = JavaScriptMerger(
                backup_enabled=self.backup_enabled.get(),
                callback=self.log_message
            )
            
            # Lire le fichier HTML
            html_file = self.html_file_path.get()
            self.log_message(f"📖 Lecture du fichier HTML: {html_file}")
            
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Créer une sauvegarde si activée
            if self.backup_enabled.get():
                backup_file = merger.create_backup(html_file)
                self.log_message(f"🔒 Sauvegarde créée: {backup_file}")
            
            # Obtenir le code JavaScript à fusionner
            if self.js_source_type.get() == "file":
                with open(self.js_file_path.get(), 'r', encoding='utf-8') as f:
                    new_js_code = f.read()
                self.log_message(f"📖 Code JavaScript lu depuis: {self.js_file_path.get()}")
            else:
                new_js_code = self.js_text.get(1.0, tk.END)
                self.log_message("📖 Code JavaScript lu depuis la zone de texte")
            
            # Extraire le JavaScript du HTML
            script_pattern = r'<script>(.*?)</script>'
            script_match = re.search(script_pattern, html_content, re.DOTALL)
            
            if not script_match:
                raise ValueError("Aucun script JavaScript trouvé dans le fichier HTML")
            
            existing_js = script_match.group(1)
            self.log_message("📊 JavaScript existant extrait du HTML")
            
            # Fusionner
            self.log_message(f"🔄 Fusion en cours avec la stratégie: {self.strategy.get()}")
            merged_js, report = merger.merge_functions(existing_js, new_js_code, self.strategy.get())
            
            # Afficher le rapport
            self.display_merge_report(report)
            
            # Remplacer dans le HTML - échapper le contenu pour éviter les erreurs regex
            def replace_script(match):
                return f'<script>{merged_js}</script>'
            
            new_html = re.sub(script_pattern, replace_script, html_content, flags=re.DOTALL)
            
            # Écrire le résultat
            output_path = self.output_file_path.get() or html_file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            self.log_message(f"✅ Fusion terminée avec succès!")
            self.log_message(f"📝 Fichier de sortie: {output_path}")
            
            # Capturer la valeur pour éviter les problèmes de scope
            success_msg = f"Fusion terminée avec succès!\n\nFichier de sortie: {output_path}"
            self.root.after(0, lambda: messagebox.showinfo("Succès", success_msg))
            
        except Exception as e:
            error_msg = f"❌ Erreur lors de la fusion: {str(e)}"
            self.log_message(error_msg)
            # Capturer la valeur de l'erreur pour éviter les problèmes de scope
            error_text = str(e)
            self.root.after(0, lambda: messagebox.showerror("Erreur", error_text))
        
        finally:
            # Réactiver les contrôles
            self.root.after(0, self.merge_finished)
    
    def display_merge_report(self, report: Dict):
        """Affiche le rapport de fusion"""
        self.log_message("\n" + "="*50)
        self.log_message("📊 RAPPORT DE FUSION")
        self.log_message("="*50)
        
        if report['added']:
            self.log_message(f"\n✅ FONCTIONS AJOUTÉES ({len(report['added'])}):")
            for func in report['added']:
                self.log_message(f"   + {func}")
        
        if report['replaced']:
            self.log_message(f"\n🔄 FONCTIONS REMPLACÉES ({len(report['replaced'])}):")
            for func in report['replaced']:
                self.log_message(f"   ↻ {func}")
        
        if report['conflicts']:
            self.log_message(f"\n⚠️  CONFLITS DÉTECTÉS ({len(report['conflicts'])}):")
            for func in report['conflicts']:
                self.log_message(f"   ⚠️  {func} (examen manuel requis)")
        
        if report['skipped']:
            self.log_message(f"\n⏭️  FONCTIONS IGNORÉES ({len(report['skipped'])}):")
            for func in report['skipped']:
                self.log_message(f"   - {func}")
        
        self.log_message("="*50 + "\n")
    
    def merge_finished(self):
        """Appelé quand la fusion est terminée"""
        self.progress.stop()
        self.merge_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
    
    def cancel_operation(self):
        """Annule l'opération en cours"""
        # Note: Dans cette implémentation simplifiée, nous ne pouvons pas vraiment
        # annuler un thread en cours d'exécution de manière propre
        self.log_message("⚠️ Annulation demandée...")
        self.merge_finished()
    
    def new_project(self):
        """Démarre un nouveau projet"""
        if messagebox.askyesno("Nouveau projet", "Effacer tous les champs et recommencer?"):
            self.html_file_path.set("")
            self.js_file_path.set("")
            self.output_file_path.set("")
            self.js_text.delete(1.0, tk.END)
            self.results_text.delete(1.0, tk.END)
            self.strategy.set("smart")
            self.backup_enabled.set(True)
    
    def show_about(self):
        """Affiche les informations sur l'application"""
        about_text = """JavaScript Code Merger v1.0

Fusionneur intelligent de code JavaScript pour développeurs.

Fonctionnalités:
• Fusion automatique de nouvelles fonctions
• Stratégies de fusion intelligentes
• Sauvegarde automatique
• Interface graphique intuitive
• Gestion des conflits

Développé avec Python et Tkinter."""
        
        messagebox.showinfo("À propos", about_text)
    
    def show_help(self):
        """Affiche l'aide"""
        help_text = """Guide d'utilisation:

1. FICHIERS:
   • Sélectionnez votre fichier HTML contenant du JavaScript
   • Choisissez entre saisie directe ou fichier pour les nouvelles fonctions
   • Spécifiez un fichier de sortie (optionnel)

2. STRATÉGIES:
   • Intelligente: Analyse et décide automatiquement
   • Remplacer: Remplace toujours les fonctions existantes
   • Ajouter seulement: N'ajoute que les nouvelles fonctions

3. OPTIONS:
   • Sauvegarde automatique: Crée une copie de sécurité
   • Logs détaillés: Suivez le processus en temps réel

4. FUSION:
   • Cliquez sur "Fusionner le code"
   • Consultez les logs et le rapport de fusion
   • Vérifiez le fichier de sortie

Conseils:
• Testez toujours votre code fusionné
• Gardez les sauvegardes activées
• Examinez les conflits manuellement"""
        
        # Créer une fenêtre d'aide
        help_window = tk.Toplevel(self.root)
        help_window.title("Guide d'utilisation")
        help_window.geometry("500x400")
        
        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Arial', 10))
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state=tk.DISABLED)
    
    def run(self):
        """Lance l'application"""
        self.root.mainloop()

def main():
    """Point d'entrée principal"""
    app = JSMergerGUI()
    app.run()

if __name__ == "__main__":
    main()
