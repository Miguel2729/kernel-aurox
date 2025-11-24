import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import configparser
import zipfile
import tempfile
import subprocess
import sys
from pathlib import Path
import urllib.request
import urllib.error
import base64
import json
import threading
def get_github_file_content_raw():
    """
    Obtém o conteúdo do arquivo usando a URL raw do GitHub.
    
    Returns:
        str: Conteúdo do arquivo ou mensagem de erro
    """
    try:
        # URL raw direta do arquivo (assumindo branch 'main')
        url = "https://raw.githubusercontent.com/Miguel2729/kernel-aurox/main/kernel.py"
        
        # Criar requisição
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        # Fazer a requisição
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
            
    except urllib.error.HTTPError as e:
        return f"Erro HTTP: {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        return f"Erro de URL: {e.reason}"
    except Exception as e:
        return f"Erro inesperado: {e}"



class AuroxDistroCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Aurox Distribution Creator")
        self.root.geometry("1000x700")
        
        # Variáveis
        self.current_project_path = None
        self.current_file = None
        self.test_process = None
        self.test_running = False
        self.test_window = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Menu principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Novo Projeto", command=self.new_project)
        file_menu.add_command(label="Abrir Projeto", command=self.open_project)
        file_menu.add_command(label="Salvar", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Ferramentas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="Editor boot.ini", command=self.open_boot_editor)
        tools_menu.add_command(label="Compilador C", command=self.open_c_compiler)
        tools_menu.add_command(label="Editor init.py", command=self.open_init_editor)
        tools_menu.add_command(label="Criar .apkg", command=self.create_apkg)
        tools_menu.add_command(label="Criar .pkg", command=self.create_pkg)
        tools_menu.add_command(label="Criar .aex", command=self.create_aex)
        tools_menu.add_command(label="Gerenciar .mnt/.umnt", command=self.manage_mounts)
        
        # Menu Estrutura
        structure_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Estrutura", menu=structure_menu)
        structure_menu.add_command(label="Explorar Arquivos", command=self.explore_files)
        structure_menu.add_command(label="Criar Sistema", command=self.create_system_structure)
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split panes
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Frame esquerdo - Navegador de arquivos
        self.left_frame = ttk.Frame(paned_window)
        paned_window.add(self.left_frame, weight=1)
        
        self.setup_file_explorer()
        
        # Frame direito - Editor
        self.right_frame = ttk.Frame(paned_window)
        paned_window.add(self.right_frame, weight=3)
        
        self.setup_editor()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Pronto")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_file_explorer(self):
        # Toolbar do explorador
        explorer_toolbar = ttk.Frame(self.left_frame)
        explorer_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(explorer_toolbar, text="↻", command=self.refresh_explorer).pack(side=tk.LEFT)
        ttk.Button(explorer_toolbar, text="+ Pasta", command=self.create_folder).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(explorer_toolbar, text="+ Arquivo", command=self.create_file).pack(side=tk.LEFT, padx=(5,0))
        
        # Treeview para arquivos
        self.tree = ttk.Treeview(self.left_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.heading("#0", text="Estrutura do Projeto")
        
        # Bind duplo clique
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
    def setup_editor(self):
        # Toolbar do editor
        editor_toolbar = ttk.Frame(self.right_frame)
        editor_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(editor_toolbar, text="Salvar", command=self.save_file).pack(side=tk.LEFT)
        ttk.Button(editor_toolbar, text="Executar", command=self.run_code).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(editor_toolbar, text="Testar Distro", command=self.test_distribution).pack(side=tk.LEFT, padx=(5,0))
        
        # Área do editor
        self.editor_frame = ttk.Frame(self.right_frame)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_editor = scrolledtext.ScrolledText(
            self.editor_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            background="black",
            foreground="white"
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Configurar tags para syntax highlighting básico
        self.setup_syntax_highlighting()
    
    def test_distribution(self):
        """Testa a distribuição Aurox com I/O em tempo real"""
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Abra um projeto Aurox primeiro")
            return
        
        # Criar janela de teste
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("Testador de Distribuição Aurox")
        self.test_window.geometry("800x600")
        
        # Frame principal
        main_frame = ttk.Frame(self.test_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Área de output
        ttk.Label(main_frame, text="Saída do Kernel:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="black",
            fg="white",
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar cores do terminal
        self.setup_terminal_colors()
        
        # Área de input
        ttk.Label(main_frame, text="Comando:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_entry = ttk.Entry(input_frame, font=("Consolas", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.input_entry.bind("<Return>", self.send_command)
        
        ttk.Button(input_frame, text="Enviar", command=self.send_command).pack(side=tk.RIGHT)
        
        # Botões de controle
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="▶Iniciar", command=self.start_distro_test).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(control_frame, text="Parar", command=self.stop_distro_test).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(control_frame, text="Limpar", command=self.clear_output).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Salvar Log", command=self.save_log).pack(side=tk.RIGHT)
        
        # Bind para fechar a janela corretamente
        self.test_window.protocol("WM_DELETE_WINDOW", self.stop_distro_test)
        
        self.append_output("[Testador de Distribuição pronto!\n")
        self.append_output("Clique em 'Iniciar' para testar sua distribuição Aurox\n")

    def setup_terminal_colors(self):
        """Configura as cores básicas do terminal"""
        # Cores 4-bit
        colors_4bit = {
            '30': '#000000', '31': '#FF0000', '32': '#00FF00', '33': '#FFFF00',
            '34': '#0000FF', '35': '#FF00FF', '36': '#00FFFF', '37': '#FFFFFF',
            '90': '#808080', '91': '#FF8080', '92': '#80FF80', '93': '#FFFF80',
            '94': '#8080FF', '95': '#FF80FF', '96': '#80FFFF', '97': '#FFFFFF'
        }
        
        for code, color in colors_4bit.items():
            self.output_text.tag_configure(f"color_{code}", foreground=color)
        
        # Tag reset
        self.output_text.tag_configure("reset", foreground="white")

    def start_distro_test(self):
        """Inicia o teste da distribuição"""
        if self.test_running:
            self.append_output("⚠Teste já está em execução\n")
            return
        
        try:
            # Verificar se o kernel.py existe
            kernel_path = os.path.join(self.current_project_path, "kernel.py")
            if not os.path.exists(kernel_path):
                self.append_output("kernel.py não encontrado no projeto\n")
                return
            
            # Criar processo para executar o kernel
            self.test_process = subprocess.Popen(
                [sys.executable, kernel_path],
                cwd=self.current_project_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.test_running = True
            self.append_output("Iniciando distribuição Aurox...\n")
            self.append_output(f"Diretório: {self.current_project_path}\n")
            
            # Iniciar thread para ler output
            self.output_thread = threading.Thread(target=self.read_process_output, daemon=True)
            self.output_thread.start()
            
            # Focar no input
            self.input_entry.focus()
            
        except Exception as e:
            self.append_output(f"Erro ao iniciar teste: {e}\n")

    def stop_distro_test(self):
        """Para o teste da distribuição"""
        if self.test_process and self.test_running:
            try:
                self.test_process.terminate()
                self.test_process.wait(timeout=5)
            except:
                self.test_process.kill()
            finally:
                self.test_running = False
                self.append_output("Teste interrompido\n")
        
        if hasattr(self, 'test_window') and self.test_window:
            self.test_window.destroy()
            self.test_window = None

    def read_process_output(self):
        """Lê o output do processo em tempo real"""
        while self.test_running and self.test_process:
            try:
                output = self.test_process.stdout.readline()
                if output:
                    self.append_output(output)
                    
                elif self.test_process.poll() is not None:
                    break
            except:
                break
        
        # Processo terminou
        if self.test_running:
            self.append_output("Processo terminou\n")
            self.test_running = False

    def send_command(self, event=None):
        """Envia comando para o processo"""
        if not self.test_running or not self.test_process:
            self.append_output("⚠Nenhum teste em execução\n")
            return
        
        command = self.input_entry.get().strip()
        if not command:
            return
        
        try:
            self.append_output(f"{command}\n")
            self.test_process.stdin.write(command + "\n")
            self.test_process.stdin.flush()
            self.input_entry.delete(0, tk.END)
        
        except Exception as e:
            self.append_output(f"Erro ao enviar comando: {e}\n")

    def append_output(self, text):
        """Adiciona texto à área de output processando cores"""
        def update_output():
            if hasattr(self, 'output_text') and self.output_text.winfo_exists():
                self.output_text.config(state=tk.NORMAL)
                
                # Processar cores básicas
                clean_text = ""
                i = 0
                while i < len(text):
                    if text[i:i+2] == '\033[':
                        end = text.find('m', i)
                        if end != -1:
                            code_str = text[i+2:end]
                            codes = code_str.split(';')
                            
                            # Reset (0)
                            if codes[0] == '0':
                                self.output_text.insert(tk.END, "", "reset")
                            
                            # 4-bit colors
                            elif codes[0] in ['30','31','32','33','34','35','36','37','90','91','92','93','94','95','96','97']:
                                tag_name = f"color_{codes[0]}"
                                content = text[end+1:text.find('\033[', end+1) or len(text)]
                                self.output_text.insert(tk.END, content, tag_name)
                                clean_text += content
                                i = end + len(content) + 1
                                continue
                            
                            # 8-bit colors (38;5;n)
                            elif len(codes) >= 3 and codes[0] == '38' and codes[1] == '5':
                                color_code = codes[2]
                                tag_name = f"color_8bit_{color_code}"
                                if tag_name not in self.output_text.tag_names():
                                    color = self.get_8bit_color(color_code)
                                    self.output_text.tag_configure(tag_name, foreground=color)
                                
                                content = text[end+1:text.find('\033[', end+1) or len(text)]
                                self.output_text.insert(tk.END, content, tag_name)
                                clean_text += content
                                i = end + len(content) + 1
                                continue
                    
                    # Caractere normal
                    clean_text += text[i]
                    self.output_text.insert(tk.END, text[i])
                    i += 1
                
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
        
        self.root.after(0, update_output)

    def get_8bit_color(self, code):
        """Retorna cor 8-bit (256 cores) simplificada"""
        try:
            idx = int(code)
            
            if idx < 16:
                # Reusa cores 4-bit
                colors_4bit = {
                    '0': '#000000', '1': '#FF0000', '2': '#00FF00', '3': '#FFFF00',
                    '4': '#0000FF', '5': '#FF00FF', '6': '#00FFFF', '7': '#FFFFFF',
                    '8': '#808080', '9': '#FF8080', '10': '#80FF80', '11': '#FFFF80',
                    '12': '#8080FF', '13': '#FF80FF', '14': '#80FFFF', '15': '#FFFFFF'
                }
                return colors_4bit.get(str(idx), '#FFFFFF')
            elif idx < 232:
                # Cores RGB
                idx -= 16
                r = (idx // 36) * 51
                g = ((idx % 36) // 6) * 51
                b = (idx % 6) * 51
                return f'#{r:02x}{g:02x}{b:02x}'
            else:
                # Escala de cinza
                gray = (idx - 232) * 10 + 8
                return f'#{gray:02x}{gray:02x}{gray:02x}'
        except:
            return '#FFFFFF'

    def clear_output(self):
        """Limpa a área de output"""
        if hasattr(self, 'output_text') and self.output_text.winfo_exists():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state=tk.DISABLED)

    def save_log(self):
        """Salva o log do teste"""
        if hasattr(self, 'output_text') and self.output_text.winfo_exists():
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt")]
            )
            if filename:
                try:
                    content = self.output_text.get(1.0, tk.END)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.append_output(f"💾 Log salvo em: {filename}\n")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar log: {e}")
    
    def setup_syntax_highlighting(self):
        # Configurações básicas de syntax highlighting para Python
        self.text_editor.tag_configure("keyword", foreground="#006EFF")
        self.text_editor.tag_configure("string", foreground="orange")
        self.text_editor.tag_configure("comment", foreground="green")
        self.text_editor.tag_configure("function", foreground="#FC69FF")
        self.text_editor.tag_configure("number", foreground="darkred")
        self.text_editor.tag_configure("bool", foreground="#0099CC")
        self.text_editor.tag_configure("decorator", foreground="#9800FF")
        self.text_editor.tag_configure("aurox_func", foreground="#00FF94")
        
        # Bind eventos para syntax highlighting
        self.text_editor.bind("<KeyRelease>", self.on_key_release)
        
    def on_key_release(self, event=None):
        # Usar after_idle para melhor performance
        self.root.after_idle(self.highlight_syntax)
        
    def highlight_syntax(self):
        # Limpar tags anteriores
        for tag in ["keyword", "string", "comment", "function", "number", "bool"]:
            self.text_editor.tag_remove(tag, "1.0", tk.END)
            
        content = self.text_editor.get("1.0", tk.END)
        
        # Destacar comentários PRIMEIRO (para evitar conflitos)
        self.highlight_comments()
        self.highlight_decorators()
        
        # Destacar strings SEGUNDO
        self.highlight_strings()
        
        self.highlight_functions()
        self.highlight_aurox_funcs()
        
        # Destacar números
        self.highlight_numbers()
        
        # Suas keywords já funcionam, então mantemos como está
        self.highlight_keywords()
        self.highlight_bools()
        
    def highlight_keywords(self):
        # Palavras-chave Python (seu código original que funciona)
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
            'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
            'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        
        for keyword in keywords:
            start = "1.0"
            while True:
                start = self.text_editor.search(rf'\y{keyword}\y', start, stopindex=tk.END, regexp=True)
                if not start:
                    break
                end = f"{start}+{len(keyword)}c"
                self.text_editor.tag_add("keyword", start, end)
                start = end

    def highlight_aurox_funcs(self):
        aurox_functions = ["VED", "matar_proc", "listar_proc", "IPC", "ler_IPC", "limpar_IPC", "criar_processo_filho", "listpkg", "usepkg", "checkpkg", "os", "time", "shutil", "random", "import2", "sys_pid", "domestico", "LFV", "keyboard", "__colors__", "gdioad", "sharedata", "user_files", "login", "reg_user", "del_user", "mnt", "umnt", "configurar_fs", "MCA", "distro", "pwroff_krnl", "debug", "CPFS", "initapp", "reboot", "installpkg", "delpkg", "addperm", "delperm", "default_perm", "auroxperm", "LinuxFs", "exec_aex", "APPC", "SYSC", "perm_padrao", "appperms"]
        
        for func in aurox_functions:
            start = "1.0"
            while True:
                start = self.text_editor.search(rf'\y{func}\y', start, stopindex=tk.END, regexp=True)
                if not start:
                    break
                end = f"{start}+{len(func)}c"
                self.text_editor.tag_add("aurox_func", start, end)
                start = end
    def highlight_bools(self):
        # Palavras-chave Python (seu código original que funciona)
        bools = ["None", "True", "False"]
        
        for bool in bools:
            start = "1.0"
            while True:
                start = self.text_editor.search(rf'\y{bool}\y', start, stopindex=tk.END, regexp=True)
                if not start:
                    break
                end = f"{start}+{len(bool)}c"
                self.text_editor.tag_add("bool", start, end)
                start = end
    def highlight_functions(self):
        funcs = [namef for namef in dir(__builtins__)]
        
        for func in funcs:
            start = "1.0"
            while True:
                start = self.text_editor.search(rf'\y{func}\y', start, stopindex=tk.END, regexp=True)
                if not start:
                    break
                end = f"{start}+{len(func)}c"
                self.text_editor.tag_add("function", start, end)
                start = end
                
    def highlight_comments(self):
        # Destacar comentários completos (tudo após # até o fim da linha)
        start = "1.0"
        while True:
            start = self.text_editor.search(r'#', start, stopindex=tk.END)
            if not start:
                break
            # Encontrar o fim da linha
            end = self.text_editor.search(r'$', start, stopindex=tk.END, regexp=True)
            if not end:
                end = tk.END
            self.text_editor.tag_add("comment", start, end)
            start = end

    def highlight_decorators(self):
        start = "1.0"
        while True:
            start = self.text_editor.search(r'@', start, stopindex=tk.END)
            if not start:
                break
            # Encontrar o fim da linha
            end = self.text_editor.search(r'$', start, stopindex=tk.END, regexp=True)
            if not end:
                end = tk.END
            self.text_editor.tag_add("decorator", start, end)
            start = end
            
    def highlight_strings(self):
        content = self.text_editor.get("1.0", tk.END)
    
        # Para aspas duplas
        start_idx = 0
        while True:
            start_idx = content.find('"', start_idx)
            if start_idx == -1:
                break
            
            end_idx = content.find('"', start_idx + 1)
            if end_idx == -1:
                break
            
            # Converter índices para posições do tkinter
            start_pos = f"1.0+{start_idx}c"
            end_pos = f"1.0+{end_idx + 1}c"
        
            self.text_editor.tag_add("string", start_pos, end_pos)
            start_idx = end_idx + 1
    
        # Para aspas simples
        start_idx = 0
        while True:
            start_idx = content.find("'", start_idx)
            if start_idx == -1:
                break
            
            end_idx = content.find("'", start_idx + 1)
            if end_idx == -1:
                break
            
            start_pos = f"1.0+{start_idx}c"
            end_pos = f"1.0+{end_idx + 1}c"
        
            self.text_editor.tag_add("string", start_pos, end_pos)
            start_idx = end_idx + 1
                        
            
    def highlight_numbers(self):
        # Destacar números
        start = "1.0"
        while True:
            start = self.text_editor.search(r'\y\d+\y', start, stopindex=tk.END, regexp=True)
            if not start:
                break
            end = self.text_editor.search(r'\M', start, stopindex=tk.END, regexp=True)
            if not end:
                end = tk.END
            self.text_editor.tag_add("number", start, end)
            start = end
            
    def new_project(self):
        path = filedialog.askdirectory(title="Selecione a pasta para o novo projeto")
        if path:
            self.current_project_path = path
            self.create_system_structure()
            self.refresh_explorer()
            self.status_bar.config(text=f"Projeto criado em: {path}")
            
    def open_project(self):
        path = filedialog.askdirectory(title="Selecione a pasta do projeto")
        if path:
            self.current_project_path = path
            self.refresh_explorer()
            self.status_bar.config(text=f"Projeto aberto: {path}")
            
    def refresh_explorer(self):
        if not self.current_project_path:
            return
            
        self.tree.delete(*self.tree.get_children())
        
        def populate_tree(parent, path):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        node = self.tree.insert(parent, "end", text=item, values=[item_path])
                        populate_tree(node, item_path)
                    else:
                        self.tree.insert(parent, "end", text=item, values=[item_path])
            except PermissionError:
                pass
                
        root_node = self.tree.insert("", "end", text=os.path.basename(self.current_project_path), 
                                   values=[self.current_project_path])
        populate_tree(root_node, self.current_project_path)
        
    def on_tree_double_click(self, event):
        item = self.tree.selection()[0]
        path = self.tree.item(item, "values")[0]
        
        if os.path.isfile(path):
            self.open_file(path)
            
    def open_file(self, path):
        if path.endswith("kernel.py"):
            messagebox.showerror("erro", "voce não pode abrir o kernel porque ele ira travar o editor")
            return
        try:
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)
            self.current_file = path
            self.status_bar.config(text=f"Editando: {os.path.basename(path)}")
            
            # Aplicar syntax highlighting
            self.highlight_syntax()
            
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin-1') as file:
                content = file.read()
                
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)
            self.current_file = path
            self.status_bar.config(text=f"Editando: {os.path.basename(path)}")
            # Aplicar syntax highlighting
            self.highlight_syntax()
        except Exception as e:
            messagebox.showerror("erro", f"erro ao abrir arquivo: {e}")
            
            
    def save_file(self):
        if not self.current_file:
            messagebox.showwarning("Aviso", "Nenhum arquivo aberto para salvar")
            return
            
        try:
            content = self.text_editor.get("1.0", tk.END)
            with open(self.current_file, 'w', encoding='utf-8') as file:
                file.write(content.rstrip())
                
            self.status_bar.config(text=f"Arquivo salvo: {os.path.basename(self.current_file)}")
            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")
            
    def create_folder(self):
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Abra um projeto primeiro")
            return
            
        folder_name = tk.simpledialog.askstring("Nova Pasta", "Nome da pasta:")
        if folder_name:
            try:
                os.makedirs(os.path.join(self.current_project_path, folder_name), exist_ok=True)
                self.refresh_explorer()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar pasta: {e}")
                
    def create_file(self):
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Abra um projeto primeiro")
            return
            
        file_name = tk.simpledialog.askstring("Novo Arquivo", "Nome do arquivo:")
        if file_name:
            try:
                with open(os.path.join(self.current_project_path, file_name), 'w') as f:
                    f.write("")
                self.refresh_explorer()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar arquivo: {e}")
                
    def run_code(self):
        if not self.current_file or not self.current_file.endswith('.py'):
            messagebox.showwarning("Aviso", "Abra um arquivo Python para executar")
            return
            
        try:
            content = self.text_editor.get("1.0", tk.END)
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
                
            # Executar
            result = subprocess.run([sys.executable, temp_path], 
                                  capture_output=True, text=True, timeout=30)
            
            # Mostrar resultado
            output_window = tk.Toplevel(self.root)
            output_window.title("Saída do Programa")
            output_window.geometry("600x400")
            
            output_text = scrolledtext.ScrolledText(output_window, wrap=tk.WORD)
            output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            if result.stdout:
                output_text.insert(tk.END, "STDOUT:\n" + result.stdout)
            if result.stderr:
                output_text.insert(tk.END, "\nSTDERR:\n" + result.stderr)
            if result.returncode != 0:
                output_text.insert(tk.END, f"\nCódigo de saída: {result.returncode}")
                
            output_text.config(state=tk.DISABLED)
            
            # Limpar arquivo temporário
            os.unlink(temp_path)
            
        except subprocess.TimeoutExpired:
            messagebox.showerror("Erro", "Tempo limite excedido")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar código: {e}")
            
    def create_system_structure(self):
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Crie ou abra um projeto primeiro")
            return
            
        estrutura = {
            'kernel.py': get_github_file_content_raw(),
            'system': {
                'apps': {},
                'code': {'init.py': 'print("Distribuição Aurox inicializada!")\n'},
                'modules': {},
                'tmp': {},
                'etc': {
                    'shells.txt': 'default[',
                    'shell.txt': 'default',
                    'systemd': {
                        "systemd.py": """# modifique isso para seu codigo do systemd
pass
""",
                        "usb.mnt": """[conf]
cond = any(os.path.exists(f'/media/usb{i}') for i in range(10))
fsname = pen-drive
fs = /dev/sdb1
mount_script = |
    import threading
    import time
    import shutil
    import os
    
    def sync_pen_drive():
        while os.path.exists('../mnt/pen-drive'):
            # Encontrar pen-drive real
            pen_drive_path = None
            for i in range(10):
                test_path = f'/media/usb{i}'
                if os.path.exists(test_path):
                    pen_drive_path = test_path
                    break
            
            if pen_drive_path:
                mount_point = '../mnt/pen-drive'
                
                # Sincronização bidirecional
                try:
                    # Do pen-drive para filesystem Aurox
                    for item in os.listdir(pen_drive_path):
                        src = os.path.join(pen_drive_path, item)
                        dst = os.path.join(mount_point, item)
                        if os.path.isfile(src) and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
                            shutil.copy2(src, dst)
                    
                    # Do filesystem Aurox para pen-drive (opcional)
                    for item in os.listdir(mount_point):
                        if item not in ['hardware.info', 'servico_hardware.status']:
                            src = os.path.join(mount_point, item)
                            dst = os.path.join(pen_drive_path, item)
                            if os.path.isfile(src) and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
                                shutil.copy2(src, dst)
                except Exception as e:
                    print(f"Erro na sincronização: {e}")
            
            time.sleep(2)  # Sincronizar a cada 2 segundos
    
    # Iniciar sincronização em thread separada
    sync_thread = threading.Thread(target=sync_pen_drive, daemon=True)
    sync_thread.start()
    
    configurar_fs('pen-drive', 'hardware', 'portable0', {'aut': True})
wait = 5
""",
                        "usb.umnt": """[conf]
cond = not any(os.path.exists(f'/media/usb{i}') for i in range(10)) and os.path.exists('../mnt/pen-drive')
fsname = pen-drive
wait = 5
"""
                    },
                    "interpr": {}
                },
                'lib32': {},
                'lib64': {},
                'framework': {},
                'shell.py': '''# Shell que chama o shell host
import os
while True:
	pidsh = os.getpid() # chama o os.getpid modificado do aurox
	sim, rem, msg = ler_IPC()
	if sim:
		os.system(msg)
'''
            },
            'pkg': {},
            'mnt': {},
            'boot.ini': '''[boot]
not_init = init.py
init = default
sh_arch = 64
force_debug = False
libp = 64

[compatibility]
s_hostsys = posix, nt
perms_default = {"net": True, "matar": True, "matarsys": False, "filesystems": False, "ambiente": False, "sistema": False, "acesso_arquivos": False}
gc = True
compile_binarys = True
disable_ioput = False
'''
        }
        
        def criar_estrutura(base_path, estrutura):
            for nome, conteudo in estrutura.items():
                path = os.path.join(base_path, nome)
                if isinstance(conteudo, dict):
                    os.makedirs(path, exist_ok=True)
                    criar_estrutura(path, conteudo)
                else:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(conteudo)
                        
        try:
            criar_estrutura(self.current_project_path, estrutura)
            self.refresh_explorer()
            messagebox.showinfo("Sucesso", "Estrutura do sistema criada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar estrutura: {e}")
            
    def open_boot_editor(self):
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Abra um projeto primeiro")
            return
            
        boot_window = tk.Toplevel(self.root)
        boot_window.title("Editor boot.ini")
        boot_window.geometry("600x500")
        
        boot_file = os.path.join(self.current_project_path, "boot.ini")
        
        # Carregar configuração atual
        config = configparser.ConfigParser()
        if os.path.exists(boot_file):
            config.read(boot_file)
        else:
            config['boot'] = {}
            config['compatibility'] = {}
            
        # Frame principal
        main_frame = ttk.Frame(boot_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba Boot
        boot_frame = ttk.Frame(notebook)
        notebook.add(boot_frame, text="Boot")
        
        ttk.Label(boot_frame, text="Arquivos não inicializar:").grid(row=0, column=0, sticky="w", pady=5)
        not_init_var = tk.StringVar(value=config.get('boot', 'not_init', fallback='init.py'))
        ttk.Entry(boot_frame, textvariable=not_init_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(boot_frame, text="Inicialização:").grid(row=1, column=0, sticky="w", pady=5)
        init_var = tk.StringVar(value=config.get('boot', 'init', fallback='default'))
        ttk.Entry(boot_frame, textvariable=init_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(boot_frame, text="Arquitetura Shell:").grid(row=2, column=0, sticky="w", pady=5)
        sh_arch_var = tk.StringVar(value=config.get('boot', 'sh_arch', fallback='64'))
        arch_combo = ttk.Combobox(boot_frame, textvariable=sh_arch_var, values=['8', '16', '32', '64'])
        arch_combo.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(boot_frame, text="Debug Forçado:").grid(row=3, column=0, sticky="w", pady=5)
        debug_var = tk.BooleanVar(value=config.getboolean('boot', 'force_debug', fallback=False))
        ttk.Checkbutton(boot_frame, variable=debug_var).grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Aba Compatibilidade
        compat_frame = ttk.Frame(notebook)
        notebook.add(compat_frame, text="Compatibilidade")
        
        ttk.Label(compat_frame, text="Sistemas Suportados:").grid(row=0, column=0, sticky="w", pady=5)
        hostsys_var = tk.StringVar(value=config.get('compatibility', 's_hostsys', fallback='posix, nt'))
        ttk.Entry(compat_frame, textvariable=hostsys_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(compat_frame, text="Permissões Padrão:").grid(row=1, column=0, sticky="w", pady=5)
        perms_var = tk.StringVar(value=config.get('compatibility', 'perms_default', fallback='{"net": True, "matar": True, "matarsys": False, "filesystems": False, "ambiente": False, "sistema": False, "acesso_arquivos": False}'))
        ttk.Entry(compat_frame, textvariable=perms_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(compat_frame, text="Garbage Collector:").grid(row=2, column=0, sticky="w", pady=5)
        gc_var = tk.BooleanVar(value=config.getboolean('compatibility', 'gc', fallback=True))
        ttk.Checkbutton(compat_frame, variable=gc_var).grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        ttk.Label(compat_frame, text="Arquitetura Lib:").grid(row=3, column=0, sticky="w", pady=5)
        libp_var = tk.StringVar(value=config.get('compatibility', 'libp', fallback='64'))
        libp_combo = ttk.Combobox(compat_frame, textvariable=libp_var, values=['32', '64'])
        libp_combo.grid(row=3, column=1, pady=5, padx=5)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def salvar_boot_ini():
            try:
                config['boot'] = {
                    'not_init': not_init_var.get(),
                    'init': init_var.get(),
                    'sh_arch': sh_arch_var.get(),
                    'force_debug': str(debug_var.get()),
                     'libp': libp_var.get()
                }
                
                config['compatibility'] = {
                    's_hostsys': hostsys_var.get(),
                    'perms_default': perms_var.get(),
                    'gc': str(gc_var.get()),
                    'compile_binarys': 'True',
                    'disable_ioput': 'False'
                }
                
                with open(boot_file, 'w') as f:
                    config.write(f)
                    
                messagebox.showinfo("Sucesso", "boot.ini salvo com sucesso!")
                boot_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar boot.ini: {e}")
                
        ttk.Button(button_frame, text="Salvar", command=salvar_boot_ini).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=boot_window.destroy).pack(side=tk.RIGHT)
        
    def open_c_compiler(self):
        compiler_window = tk.Toplevel(self.root)
        compiler_window.title("Compilador C")
        compiler_window.geometry("500x400")
        
        main_frame = ttk.Frame(compiler_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Arquivo C de entrada:").pack(anchor="w", pady=5)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=input_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(input_frame, text="Procurar", command=lambda: self.browse_file(input_var, [("C files", "*.c")])).pack(side=tk.RIGHT)
        
        ttk.Label(main_frame, text="Saída:").pack(anchor="w", pady=5)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(output_frame, text="Procurar", command=lambda: self.browse_save_file(output_var, [("Library files", "*.so *.dll")])).pack(side=tk.RIGHT)
        
        ttk.Label(main_frame, text="Plataforma:").pack(anchor="w", pady=5)
        platform_var = tk.StringVar(value="linux")
        platform_combo = ttk.Combobox(main_frame, textvariable=platform_var, values=["linux", "windows"])
        platform_combo.pack(fill=tk.X, pady=5)
        
        ttk.Label(main_frame, text="Arquitetura:").pack(anchor="w", pady=5)
        arch_var = tk.StringVar(value="64")
        arch_combo = ttk.Combobox(main_frame, textvariable=arch_var, values=["32", "64"])
        arch_combo.pack(fill=tk.X, pady=5)
        
        # Área de log
        ttk.Label(main_frame, text="Log:").pack(anchor="w", pady=(10,0))
        log_text = scrolledtext.ScrolledText(main_frame, height=10)
        log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        def compilar():
            input_file = input_var.get()
            output_file = output_var.get()
            platform = platform_var.get()
            arch = arch_var.get()
            
            if not input_file or not output_file:
                messagebox.showwarning("Aviso", "Selecione arquivos de entrada e saída")
                return
                
            try:
                log_text.delete("1.0", tk.END)
                log_text.insert(tk.END, f"Compilando {input_file}...\n")
                
                # Comandos de compilação básicos
                if platform == "linux":
                    cmd = ["gcc", "-shared", "-fPIC"]
                    if arch == "64":
                        cmd.extend(["-m64"])
                    else:
                        cmd.extend(["-m32"])
                    cmd.extend([input_file, "-o", output_file])
                    ext = ".so"
                else:  # windows
                    cmd = ["gcc", "-shared"]
                    cmd.extend([input_file, "-o", output_file])
                    ext = ".dll"
                    
                # Garantir extensão correta
                if not output_file.endswith(ext):
                    output_var.set(output_file + ext)
                    output_file += ext
                    
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    log_text.insert(tk.END, "Compilação bem-sucedida!\n")
                    messagebox.showinfo("Sucesso", "Arquivo compilado com sucesso!")
                else:
                    log_text.insert(tk.END, f"Erro na compilação:\n{result.stderr}\n")
                    messagebox.showerror("Erro", "Falha na compilação")
                    
            except Exception as e:
                log_text.insert(tk.END, f"Erro: {e}\n")
                messagebox.showerror("Erro", f"Erro durante a compilação: {e}")
                
        ttk.Button(main_frame, text="Compilar", command=compilar).pack(pady=10)
        
    def browse_file(self, var, filetypes):
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            var.set(filename)
            
    def browse_save_file(self, var, filetypes):
        filename = filedialog.asksaveasfilename(filetypes=filetypes)
        if filename:
            var.set(filename)
            
    def open_init_editor(self):
        if not self.current_project_path:
            messagebox.showwarning("Aviso", "Abra um projeto primeiro")
            return
            
        init_file = os.path.join(self.current_project_path, "system", "code", "init.py")
        if os.path.exists(init_file):
            self.open_file(init_file)
        else:
            messagebox.showinfo("Info", "init.py não encontrado. Crie a estrutura do sistema primeiro.")
            
    def create_apkg(self):
        self.show_package_creator("apkg")
        
    def create_pkg(self):
        self.show_package_creator("pkg")
        
    def create_aex(self):
        self.show_package_creator("aex")
        
    def show_package_creator(self, package_type):
        creator_window = tk.Toplevel(self.root)
        creator_window.title(f"Criar .{package_type.upper()}")
        creator_window.geometry("600x500")
        
        main_frame = ttk.Frame(creator_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba Informações Básicas
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Informações")
        
        ttk.Label(info_frame, text="Nome do Pacote:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(info_frame, text="Versão:").grid(row=1, column=0, sticky="w", pady=5)
        version_var = tk.StringVar(value="1.0")
        ttk.Entry(info_frame, textvariable=version_var, width=40).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(info_frame, text="Autor:").grid(row=2, column=0, sticky="w", pady=5)
        author_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=author_var, width=40).grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(info_frame, text="Descrição:").grid(row=3, column=0, sticky="w", pady=5)
        desc_text = scrolledtext.ScrolledText(info_frame, height=4, width=40)
        desc_text.grid(row=3, column=1, pady=5, padx=5)
        
        # Aba Conteúdo
        content_frame = ttk.Frame(notebook)
        notebook.add(content_frame, text="Conteúdo")
        
        ttk.Label(content_frame, text="Arquivos para incluir:").pack(anchor="w", pady=5)
        
        files_frame = ttk.Frame(content_frame)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        files_listbox = tk.Listbox(files_frame)
        files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_buttons = ttk.Frame(files_frame)
        files_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        
        def add_files():
            files = filedialog.askopenfilenames()
            for file in files:
                files_listbox.insert(tk.END, file)
                
        def remove_file():
            selection = files_listbox.curselection()
            if selection:
                files_listbox.delete(selection[0])
                
        ttk.Button(files_buttons, text="Adicionar", command=add_files).pack(fill=tk.X, pady=2)
        ttk.Button(files_buttons, text="Remover", command=remove_file).pack(fill=tk.X, pady=2)
        
        # Botão criar
        def criar_pacote():
            name = name_var.get()
            if not name:
                messagebox.showwarning("Aviso", "Digite um nome para o pacote")
                return
                
            try:
                output_file = filedialog.asksaveasfilename(
                    defaultextension=f".{package_type}",
                    filetypes=[(f"{package_type.upper()} files", f"*.{package_type}")]
                )
                
                if output_file:
                    with zipfile.ZipFile(output_file, 'w') as zipf:
                        # Adicionar arquivos selecionados
                        for i in range(files_listbox.size()):
                            file_path = files_listbox.get(i)
                            zipf.write(file_path, os.path.basename(file_path))
                            
                        # Adicionar metadados
                        metadata = {
                            'name': name,
                            'version': version_var.get(),
                            'author': author_var.get(),
                            'description': desc_text.get("1.0", tk.END).strip(),
                            'type': package_type
                        }
                        
                        zipf.writestr('metadata.txt', str(metadata))
                        
                    messagebox.showinfo("Sucesso", f"Pacote .{package_type} criado com sucesso!")
                    creator_window.destroy()
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar pacote: {e}")
                
        ttk.Button(main_frame, text="Criar Pacote", command=criar_pacote).pack(pady=10)
        
    def manage_mounts(self):
        mount_window = tk.Toplevel(self.root)
        mount_window.title("Gerenciar .mnt/.umnt")
        mount_window.geometry("700x500")
        
        main_frame = ttk.Frame(mount_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista de configurações existentes
        ttk.Label(main_frame, text="Configurações de Mount/Unmount:").pack(anchor="w", pady=5)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        mount_listbox = tk.Listbox(list_frame)
        mount_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        list_buttons = ttk.Frame(list_frame)
        list_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        
        def carregar_configuracoes():
            mount_listbox.delete(0, tk.END)
            if not self.current_project_path:
                return
                
            systemd_path = os.path.join(self.current_project_path, "system/etc", "systemd")
            if os.path.exists(systemd_path):
                for file in os.listdir(systemd_path):
                    if file.endswith(('.mnt', '.umnt')):
                        mount_listbox.insert(tk.END, file)
                        
        def editar_config():
            selection = mount_listbox.curselection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione uma configuração")
                return
                
            config_file = mount_listbox.get(selection[0])
            full_path = os.path.join(self.current_project_path, "system/etc", "systemd", config_file)
            self.open_file(full_path)
            mount_window.destroy()
            
        def nova_config():
            config_window = tk.Toplevel(mount_window)
            config_window.title("Nova Configuração")
            config_window.geometry("500x400")
            
            main_config_frame = ttk.Frame(config_window)
            main_config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(main_config_frame, text="Tipo:").grid(row=0, column=0, sticky="w", pady=5)
            type_var = tk.StringVar(value="mnt")
            type_combo = ttk.Combobox(main_config_frame, textvariable=type_var, values=["mnt", "umnt"])
            type_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Nome:").grid(row=1, column=0, sticky="w", pady=5)
            name_var = tk.StringVar()
            ttk.Entry(main_config_frame, textvariable=name_var, width=30).grid(row=1, column=1, pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Condição:").grid(row=2, column=0, sticky="w", pady=5)
            cond_var = tk.StringVar(value="True")
            ttk.Entry(main_config_frame, textvariable=cond_var, width=30).grid(row=2, column=1, pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Filesystem:").grid(row=3, column=0, sticky="w", pady=5)
            fs_var = tk.StringVar()
            ttk.Entry(main_config_frame, textvariable=fs_var, width=30).grid(row=3, column=1, pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Nome FS:").grid(row=4, column=0, sticky="w", pady=5)
            fsname_var = tk.StringVar()
            ttk.Entry(main_config_frame, textvariable=fsname_var, width=30).grid(row=4, column=1, pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Script Mount:").grid(row=5, column=0, sticky="w", pady=5)
            script_var = tk.StringVar(value="pass")
            ttk.Entry(main_config_frame, textvariable=script_var, width=30).grid(row=5, column=1, pady=5, padx=5)
            
            ttk.Label(main_config_frame, text="Intervalo (segundos):").grid(row=6, column=0, sticky="w", pady=5)
            interval_var = tk.StringVar(value="5")
            ttk.Entry(main_config_frame, textvariable=interval_var, width=30).grid(row=6, column=1, pady=5, padx=5)
            
            def salvar_config():
                try:
                    config = configparser.ConfigParser()
                    config['conf'] = {
                        'cond': cond_var.get(),
                        'fsname': fsname_var.get(),
                        'fs': fs_var.get(),
                        'mount_script': script_var.get(),
                        'wait': interval_var.get()
                    }
                    
                    filename = f"{name_var.get()}.{type_var.get()}"
                    full_path = os.path.join(self.current_project_path, "system/etc", "systemd", filename)
                    
                    with open(full_path, 'w') as f:
                        config.write(f)
                        
                    messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
                    config_window.destroy()
                    carregar_configuracoes()
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar configuração: {e}")
                    
            ttk.Button(main_config_frame, text="Salvar", command=salvar_config).grid(row=7, column=1, sticky="e", pady=10)
            
        ttk.Button(list_buttons, text="Nova", command=nova_config).pack(fill=tk.X, pady=2)
        ttk.Button(list_buttons, text="Editar", command=editar_config).pack(fill=tk.X, pady=2)
        ttk.Button(list_buttons, text="Excluir", command=lambda: self.excluir_config(mount_listbox, carregar_configuracoes)).pack(fill=tk.X, pady=2)
        ttk.Button(list_buttons, text="Atualizar", command=carregar_configuracoes).pack(fill=tk.X, pady=2)
        
        carregar_configuracoes()
        
    def excluir_config(self, listbox, callback):
        selection = listbox.curselection()
        if not selection:
            return
            
        config_file = listbox.get(selection[0])
        full_path = os.path.join(self.current_project_path, "system/etc", "systemd", config_file)
        
        if messagebox.askyesno("Confirmar", f"Excluir {config_file}?"):
            try:
                os.remove(full_path)
                callback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}")
                
    def explore_files(self):
        if not self.current_project_path:
            self.open_project()
        if self.current_project_path:
            self.refresh_explorer()

def main():
    root = tk.Tk()
    app = AuroxDistroCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
