import threading as th
import os
import shutil
import sys
import time
for i in range(5):
	os.system("clear")
	time.sleep(1)
	print("_")
	time.sleep(0.3)
idle = True
def pwroff_krnl():
	global hw_instan
	global idle
	print("desligando...")
	time.sleep(0.4)
	print("encerrando processos...")
	time.sleep(0.3)
	for i in range(len(hw_instan.ppn)):
		a = hw_instan.ppn[i][1]
		if i not in hw_instan.processos_parar:
			hw_instan.processos_parar[hw_instan.ppn[i][0]] = True
	
		print(f"⚠️{a} encerrado")
		time.sleep(0.2)
	print("✅️processos encerrados")
	time.sleep(0.2)
	print("limpando ppn...")
	hw_instan.ppn = []
	print("✅️ppn limpado")
	time.sleep(0.2)
	print("limpando threads...")
	hw_instan.threads = []
	print("✅️limpado")
	time.sleep(0.2)
	print(f"finalizando...")
	idle = False
	quit()	

print(f"status_idle: {str(idle)}")
def initapp(app, reset_m):
	os.chdir("./apps/")
	with open(app + ".py", "r") as aplicativo:
		codigo = aplicativo.read()
		tmp_m.append([codigo, app])
		if reset_m:
			del hw_instan
			hw_instan = hardware(tmp_m)
		else:
			hw_instan.memory = tmp_m
	os.chdir("..")
			
def configurar_fs(nomefs, tipo_conectar, onde, parametros=None):
    """
    Configura e conecta filesystems montados a diversos destinos
    
    Parâmetros:
    nomefs: nome do filesystem montado
    tipo_conectar: tipo de conexão ('hardware', 'diretorio', 'codigo_paralelo', 'rede')
    onde: destino da conexão (path, dispositivo, etc)
    parametros: dicionário com parâmetros específicos do tipo
    
    Retorna:
    bool: True se configuração foi bem-sucedida
    """
    
    if parametros is None:
        parametros = {}
    
    # Verifica se o filesystem está montado
    mount_point = os.path.join('../mnt', nomefs)
    if not os.path.exists(mount_point):
        print(f"Erro: Filesystem {nomefs} não está montado")
        return False
    
    try:
        if tipo_conectar == 'hardware':
            return _conectar_hardware(nomefs, onde, parametros, mount_point)
            
        elif tipo_conectar == 'diretorio':
            return _conectar_diretorio(nomefs, onde, parametros, mount_point)
            
        elif tipo_conectar == 'codigo_paralelo':
            return _conectar_codigo_paralelo(nomefs, onde, parametros, mount_point)
            
        elif tipo_conectar == 'rede':
            return _conectar_rede(nomefs, onde, parametros, mount_point)
            
        else:
            print(f"Erro: Tipo de conexão '{tipo_conectar}' não suportado")
            return False
            
    except Exception as e:
        print(f"Erro ao configurar {nomefs}: {e}")
        return False

def _conectar_hardware(nomefs, dispositivo, parametros, mount_point):
    """Conecta FS a dispositivo de hardware simulado"""
    
    print(f"🔌 Conectando {nomefs} ao hardware {dispositivo}")
    
    # Simula diferentes tipos de hardware
    if dispositivo == 'serial':
        baud_rate = parametros.get('baud_rate', 9600)
        print(f"   Configurando serial: {baud_rate} baud")
        
        # Cria arquivo de controle do serial
        with open(os.path.join(mount_point, '.serial_config'), 'w') as f:
            f.write(f"device=serial\nbaud_rate={baud_rate}\n")
            
    elif dispositivo == 'usb':
        vid = parametros.get('vendor_id', '0x1234')
        pid = parametros.get('product_id', '0x5678')
        print(f"   Configurando USB: VID={vid}, PID={pid}")
        
        with open(os.path.join(mount_point, '.usb_config'), 'w') as f:
            f.write(f"device=usb\nvendor_id={vid}\nproduct_id={pid}\n")
            
    elif dispositivo == 'audio':
        sample_rate = parametros.get('sample_rate', 44100)
        print(f"   Configurando áudio: {sample_rate}Hz")
        
        with open(os.path.join(mount_point, '.audio_config'), 'w') as f:
            f.write(f"device=audio\nsample_rate={sample_rate}\n")
    
    else:
        print(f"   Dispositivo genérico: {dispositivo}")
        with open(os.path.join(mount_point, '.hardware_config'), 'w') as f:
            f.write(f"device={dispositivo}\n")
    
    return True

def _conectar_diretorio(nomefs, diretorio, parametros, mount_point):
    """Conecta FS a um diretório do sistema"""
    
    print(f"📁 Conectando {nomefs} ao diretório {diretorio}")
    
    # Verifica se diretório existe
    if not os.path.exists(diretorio):
        if parametros.get('criar_diretorio', False):
            os.makedirs(diretorio)
            print(f"   Diretório {diretorio} criado")
        else:
            print(f"   Erro: Diretório {diretorio} não existe")
            return False
    
    # Cria link simulado ou sincronização
    sync_mode = parametros.get('sync_mode', 'readonly')
    
    with open(os.path.join(mount_point, '.dir_connection'), 'w') as f:
        f.write(f"target_dir={diretorio}\nsync_mode={sync_mode}\n")
    
    # Se for modo espelho, copia conteúdo inicial
    if sync_mode == 'mirror':
        try:
            for item in os.listdir(diretorio):
                src = os.path.join(diretorio, item)
                dst = os.path.join(mount_point, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
            print(f"   Conteúdo espelhado de {diretorio}")
        except Exception as e:
            print(f"   Aviso: Não foi possível espelhar conteúdo: {e}")
    
    return True

def _conectar_codigo_paralelo(nomefs, codigo_file, parametros, mount_point):
    """Conecta FS a código que modifica em paralelo (restrito ao FS)"""
    
    print(f"⚡ Conectando {nomefs} a código paralelo: {codigo_file}")
    
    # Verifica se arquivo de código existe
    if not os.path.exists(codigo_file):
        print(f"   Erro: Arquivo de código {codigo_file} não existe")
        return False
    
    # Lê o código
    try:
        with open(codigo_file, 'r') as f:
            codigo = f.read()
    except Exception as e:
        print(f"   Erro ao ler código: {e}")
        return False
    
    # Verifica restrições de segurança do código
    if not _codigo_eh_seguro(codigo, mount_point):
        print(f"   Erro: Código tenta acessar fora do filesystem")
        return False
    
    # Configura execução paralela
    intervalo = parametros.get('intervalo', 5)  # segundos
    
    with open(os.path.join(mount_point, '.parallel_code'), 'w') as f:
        f.write(f"code_file={codigo_file}\ninterval={intervalo}\n")
    
    # Inicia thread para executar código periodicamente
    def executar_codigo_paralelo():
        while os.path.exists(mount_point):  # Enquanto FS estiver montado
            try:
                # Executa código no contexto do filesystem
                old_cwd = os.getcwd()
                os.chdir(mount_point)
                
                # Cria ambiente restrito
                restricted_globals = {
                    '__builtins__': {
                        'print': print,
                        'len': len,
                        'str': str,
                        'int': int,
                        'os': __import__('os'),
                        'time': __import__('time')
                    },
                    'fs_path': mount_point
                }
                
                exec(codigo, restricted_globals)
                os.chdir(old_cwd)
                
            except Exception as e:
                if debug:
                    print(f"   Erro em código paralelo {codigo_file}: {e}")
                os.chdir(old_cwd)
            
            time.sleep(intervalo)
    
    # Inicia thread
    thread_paralela = th.Thread(target=executar_codigo_paralelo, daemon=True)
    thread_paralela.start()
    
    print(f"   Código paralelo iniciado (intervalo: {intervalo}s)")
    return True

def _conectar_rede(nomefs, endpoint, parametros, mount_point):
    """Conecta FS a recurso de rede"""
    
    print(f"🌐 Conectando {nomefs} a {endpoint}")
    
    protocolo = parametros.get('protocolo', 'http')
    porta = parametros.get('porta', 80)
    
    with open(os.path.join(mount_point, '.network_config'), 'w') as f:
        f.write(f"endpoint={endpoint}\nprotocol={protocolo}\nport={porta}\n")
    
    # Simula conexão de rede
    if protocolo == 'http':
        print(f"   Configurado HTTP para {endpoint}:{porta}")
    elif protocolo == 'ftp':
        print(f"   Configurado FTP para {endpoint}:{porta}")
    elif protocolo == 'nfs':
        print(f"   Configurado NFS para {endpoint}")
    
    return True

def _codigo_eh_seguro(codigo, mount_point):
    """Verifica se código só acessa dentro do filesystem"""
    
    verificacoes_perigosas = [
        "os.chdir('..')",
        "os.chdir('/')",
        "shutil.rmtree('/')",
        "os.remove('/')",
        f"os.chdir('{mount_point}')"  # Tenta escapar via path absoluto
    ]
    
    for perigo in verificacoes_perigosas:
        if perigo in codigo:
            return False
    
    return True
    

# Mantenha as funções matar_proc e listar_proc como estão, mas adicione:

def matar_proc(pid):
    """Função para matar processo - versão final"""
    try:
        if 'hw_instan' in globals():
            # Marca para parar e remove da lista
            hw_instan.processos_parar[pid] = True
            
            if pid in hw_instan.ppn:
                nome_processo = hw_instan.ppn[pid][1]
                del hw_instan.ppn[pid]
                print(f"Processo {pid} ({nome_processo}) terminado - thread em estado pass")
            else:
                print(f"Processo {pid} não encontrado")
        else:
            print("Sistema não inicializado")
    except Exception as e:
        print(f"Erro ao matar processo {pid}: {e}")
        

def listar_proc():
    procs = []
    """Função para listar processos - versão atualizada"""
    try:
        if 'hw_instan' in globals() and hasattr(hw_instan, 'ppn'):
            processos = hw_instan.ppn
            if processos:
                print("Processos em execução:")
                for pid, info in processos.items():
                    # Mostra se o processo está marcado para parar
                    status = "🛑" if pid in getattr(hw_instan, 'processos_parar', {}) else "✅"
                    print(f"{status} PID: {pid}, Nome: {info[1]}")
                    procs.append([pid, info[1]])
            else:
                print("Nenhum processo em execução")
                return None
        else:
            print("Sistema não inicializado")
            return None
    except Exception as e:
        print(f"Erro ao listar processos: {e}")
        return None
    return procs
print(os.getcwd())
if __name__ == "__main__":
	a = input("modo debug?(S/n): ")
	if a == "S" or a == "s":
		debug = True
		del a
	else:
		debug = False
		del a

def mnt(fs, nomefs):
    """
    Simula a montagem de um sistema de arquivos no diretório ./mnt
    
    Parâmetros:
    fs: caminho ou identificador do sistema de arquivos a ser montado
    nomefs: nome do ponto de montagem ou identificador do sistema de arquivos
    
    Retorna:
    bool: True se a montagem foi bem-sucedida, False caso contrário
    """
    
    # Verifica se o diretório ./mnt existe
    if not os.path.exists('../mnt'):
        print(f"Erro: Diretório ./mnt não existe")
        return False
    
    # Verifica se ./mnt é realmente um diretório
    if not os.path.isdir('../mnt'):
        print(f"Erro: ./mnt não é um diretório")
        return False
    
    # Cria o caminho completo para o ponto de montagem
    mount_point = os.path.join('../mnt', nomefs)
    
    try:
        # Verifica se o ponto de montagem já existe
        if os.path.exists(mount_point):
            print(f"Aviso: Ponto de montagem {mount_point} já existe")
            # Pode-se optar por remover ou não o diretório existente
            # shutil.rmtree(mount_point)
            # os.makedirs(mount_point)
            return False
        
        # Cria o diretório para o ponto de montagem
        os.makedirs(mount_point)
        print(f"Sistema de arquivos '{fs}' montado em '{mount_point}'")
        
        # Aqui você pode adicionar lógica adicional para simular
        # a montagem real, como copiar conteúdo, criar estrutura, etc.
        
        # Exemplo: criar um arquivo indicando a montagem
        info_file = os.path.join(mount_point, '.mount_info')
        with open(info_file, 'w') as f:
            f.write(f"Sistema de arquivos: {fs}\n")
            f.write(f"Ponto de montagem: {nomefs}\n")
            f.write(f"Montado em: {os.path.abspath(mount_point)}\n")
        
        return True
        
    except Exception as e:
        print(f"Erro ao montar {fs} em {mount_point}: {e}")
        return False


# Função auxiliar para desmontar
def umnt(nomefs):
    """
    Simula a desmontagem de um sistema de arquivos
    
    Parâmetros:
    nomefs: nome do ponto de montagem a ser desmontado
    
    Retorna:
    bool: True se a desmontagem foi bem-sucedida, False caso contrário
    """
    
    mount_point = os.path.join('../mnt', nomefs)
    
    try:
        if not os.path.exists(mount_point):
            print(f"Erro: Ponto de montagem {mount_point} não existe")
            return False
        
        # Remove o diretório de montagem
        shutil.rmtree(mount_point)
        print(f"Sistema de arquivos desmontado de '{mount_point}'")
        return True
        
    except Exception as e:
        print(f"Erro ao desmontar {mount_point}: {e}")
        return False

 

class hardware:
    def __init__(self, m):
        self.memory = m
        self.num = -1
        self.threads = []
        self.thread_code = {}
        cput = th.Thread(target=self.cpu)
        cput.start()
        if debug: print("✅ Thread cpu iniciada")
        self.procn = 0
        self.ppn = {}
        self.processos_parar = {}
    
    def cpu(self):
        if debug: print("🔧 Método cpu() executando")
        
        # ✅ DEBUG: Mostrar o que está na memória
        if debug: 
            print(f"📝 Memória tem {len(self.memory)} aplicações:")
            for i, app in enumerate(self.memory):
                print(f"  codigo {i}: {app[0][:40]}...")
        
        for i in range(len(self.memory)):
            if i <= self.num:
                if debug: print(f"⏭️  Pulando item {i} (já processado)")
                continue
            
            try:
                if debug: print(f"🎯 Processando item {i}")
                
                # ✅ DEBUG: Apenas compilar
                if debug: 
                    print(f"🧪 Compilando código {i}...")
                
                compile(self.memory[i][0], '<string>', 'exec')
                if debug: print(f"✅ Compilação funcionou")
                
                def create_thread(pid):
                    def thread_func():
                        # ✅ WRAPPER: Adiciona verificação automática em loops
                        codigo_wrap = f"""
import time
_original_code = '''{self.memory[i][0].replace("'", "\\'")}'''

# Substitui while True por while com verificação
_code_modified = _original_code
if 'while True:' in _original_code:
    _code_modified = _original_code.replace(
        'while True:', 
        f'while {pid} not in hw_instan.processos_parar:'
    )
elif 'while True' in _original_code:
    _code_modified = _original_code.replace(
        'while True', 
        f'while {pid} not in hw_instan.processos_parar'
    )

exec(_code_modified, globals())

# Se saiu do loop, vai para estado pass
if {pid} in hw_instan.processos_parar:
    while True:
        pass
"""
                        try:
                            exec(codigo_wrap, globals())
                        except Exception as e:
                            print(f"Erro no processo {pid}: {e}")
                    return thread_func
                
                self.thread_code[self.procn] = self.memory[i][0]
                self.ppn[self.procn] = [self.procn, self.memory[i][1]]
                thread = th.Thread(target=create_thread(self.procn))
                thread.start()
                self.procn +=1
                self.threads.append(thread)
               
                if debug: print(f"✅ Thread codigo {i} iniciada como PID {self.procn-1}")
                self.num = i
                
            except Exception as e:
                if debug: print(f"❌ Erro no item {i}: {e}")
                import traceback
                traceback.print_exc()

				
if __name__ == "__main__":
	if os.path.exists("./system"):
		pass
		if debug: print("sistema existe")
	else:
		if debug: print("sistema nao existe, criando...")
		try:
			with open("./create_sys.py", "r") as cresys:
				codigo = cresys.read()
				if debug: print("codigo lido")
				exec(codigo)
				if debug: print("codigo de criacao executado")
		except Exception as e:
			print(f"erro: {e}")
			quit()
	
	tmp_m = []
	
	# tmp
	tmpd = os.getcwd() + "/system/tmp"
	os.environ['TMP'] = tmpd
	os.environ['TMPDIR'] = tmpd
	os.environ['TEMP'] = tmpd
	
	# listdirs
	root_ = os.listdir()
	system_code_ = os.listdir("./system/code")
	if debug: print(f"📁 {len(system_code_)} codigos do sistema foram encontrados")
	if "./" not in sys.path:
		sys.path.insert(0, "./")
	if "./system/modules" not in sys.path:
		sys.path.insert(0, "./system/modules")
	erro_no_tmp_m = 0
	existe_init = False
	if os.path.exists("system/code/init.py") and os.path.isfile("system/code/init.py"):
		if debug: print("📖 lendo init.py...")
		existe_init = True
		with open("system/code/init.py", "r") as initfile:
			try:
				try:
					tmp_m.append([initfile.read(), "init"])
					hw_instan = hardware(tmp_m)
					if debug: print(" ✅️ init.py inicializado na memoria")
				except Exception as e:
					if debug: print(f"erro ao ler init.py ou erro ao inicializar o init.py na memoria: {e}")
			except Exception as e:
				erro_no_tmp_m += 1
				if debug: print(f" ⚠️ falha ao abrir init.py: {e}")
				quit()
	else:
		for i, arquivos in enumerate(system_code_):
			os.chdir("./system/code")
			if arquivos.endswith(".py"):
				pass
			else:
				continue
			if debug: print(f"📖lendo arquivo {arquivos}({i})")
			with open(arquivos, "r") as code:
				try:
					tmp_m.append([code.read(), f"sys service {i}"])
					if debug: print(f" ✅️ {arquivos} adicionado ao tmp_m com sucesso(numero execucao {i})")
				except Exception as e:
					if debug: print(f" ⚠️ falha ao adicionar {arquivos}({i}) ao tmp_m: {e}")
					erro_no_tmp_m += 1
			os.chdir("../..")
	os.chdir("system")
	os.system("chmod +x ./shell")
	if debug: print("shell adicionado 'x' na permissao")
	os.system("echo './shell' | tee -a /etc/shells")
	if debug: print("shell usando")
	if debug: print(f" 💾 hardware tem {len(tmp_m)} na memoria, {erro_no_tmp_m} nao foram adicionadas por erro")
	hw_instan = hardware(tmp_m)
	# idle processo
	while idle:
		if debug: print(f"debug: idle = {idle}")
		if not idle:
			if debug: print(f"debug: idle = {idle}")
			break
		time.sleep(3)
		if not idle:
			if debug: print(f"debug: idle = {idle}")
			break
		if not idle: print(f"isso não deveria aparacer em idle = False\ntipo: {type(idle)}")
		time.sleep(25)
	# fim do idle processo
	
	
def remover_shell():
    # Pega o diretório atual + /shell
    shell_path = os.path.join(os.getcwd(), "shell")
    
    # Remove do /etc/shells (CORRIGIDO: usar \\ ou /)
    os.system(f"sed -i '\\|{shell_path}|d' /etc/shells")
    
    if debug: print(f"Shell {shell_path} removido do /etc/shells")
    
    # Verifica se ainda está listado
    os.system(f"grep -n '{shell_path}' /etc/shells")
    


