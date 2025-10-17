'''
informacoes:
	1. os processos tem acesso ao kernel porque sao executados dentro do kernel, globalmente
	2. por causa da informacao 1, apps e distruibuicoes podem usar as funcoes do kernel, elas sao, mnt, umnt, configurar_fs, classe distro, matar_proc, listar_proc, initapp, IPC, limpar_IPC, ler_IPC. VED, installpkg, delpkg, listpkg, usepkg, checkpkg, criar_processo_filho. sem importar o kernel
	3. o aurox espera essa estrutura:
		1. kernel.py - aurox
		2. system/ - arquivos da distro
		3. system/shell(arquivo sem extensao) - shell customizado
		4. system/modules - modulos da distro
		5. system/code - tem servicos da distro e o init.py
		6. apps do sistema
		7. system/apps - aplicativos do sistema(se tiver)
		8. system/tmp - arquivos temporarios
		9. mnt/
		10. pkg/
		9. mnt - lugar onde filesystems sao montados
	4. quando a distro é inicializada, o diretorio global continua sendo system
	5. o nome do kernel é aurox
	6. a classe distro configura a distro:
		1. nome dela
		2. versao dela
		3. filesystems para montar e configurar
		4. servicos para inicializar
		5. ipc
		6. ufs(umount filesystems on shutdown)
		7, pacotes
	7. isso é um kernel é não um OS, ele executa a distro(distruibuição aurox) assim como o linux exexuta a distro linux(distruibuição linux)
	8. o limite de processos é 500
	9. initapp inicializa apps e nao servicos, nao use initapp para inicializar servicos e nao coloque apps em system/code/, coloque em system/apps
	10. as distros não sao apenas a classe
	11. os processos sao executados globalmente dentro do kernel e não como modulos separados, assim, processos não precisam importar kernel e podem interagir com o kernel
'''

sys_pid = []

import threading as th
import os
import shutil
import sys
import time
import random
def boot_anim():
	for i in range(5):
		os.system("clear")
		time.sleep(1)
		print("_")
		time.sleep(0.3)
		if i == 4:
			os.system("clear")


def VSP():
	global hw_instan
	global sys_pid
	global SYSC
	sys_pid = []
	for i in range(len(hw_instan.memory)):
		if hw_instan.memory[i][2] == SYSC:
			sys_pid.append(hw_instan.ppn[i][0])
	sys_pid = tuple(sys_pid)

# (verification of existing process)
def VED(pid, nome, x):
	global hw_instan
	if x == "pid":
		# Correção: Verificar se pid existe no ppn
		if pid in hw_instan.ppn:
			nome = hw_instan.ppn[pid][1]  # Correção: acessar via ppn
			return (True, nome)
		else:
			return (False, None)
	elif x == "name":
		# Correção: Iterar sobre os itens do ppn
		for pid_atual, info in hw_instan.ppn.items():
			if info[1] == nome:  # info[1] é o nome do processo
				return (True, pid_atual)
		return (False, None)
distro_cfg = False
# (umount filesystems on shutdown)
UFS = None
# classe para as distros usarem
class distro:
	def __init__(self, nome, ver, fs, nomesfs, cfgfs, services, serv_reset_m, ipc, ufs, pkgs):
		global tmp_m, hw_instan, distro_cfg, UFS
		for pacote in pkgs:
			installpkg(pacote[0], pacote[1])
		if not distro_cfg:
			os.makedirs("./info", exist_ok=True)
			with open("./info/nome.txt", "w") as nomed:
				nomed.write(nome)
			with open("./info/ver.txt", "w") as verd:
				verd.write(ver)
			if not ipc:
				global IPC
				global limpar_IPC
				def sem_ipc():
					return None
				IPC = sem_ipc()
				limpar_IPC = sem_ipc()
			if debug: print(f"IPC = {ipc}")
			if debug: print(f"💿 distro tem {len(nomesfs)} filesystems")
			for i, nomefs in enumerate(nomesfs):
				if debug: print(f"💽 montando {nomefs}({i})...")
				try:
					mnt(fs[i], nomefs)
				except Exception as e:
					if debug:
						print(f"⛔️erro ao montar {nomefs}: {e}")
					else:
						print(f"⛔️erro: {e}")
						quit()
				if debug: print(f"⚙️ configurando {nomefs}")
				try:
					configurar_fs(nomefs, cfgfs[i][0], cfgfs[i][1], cfgfs[i][2])
				except Exception as e:
					if debug:
						print(f"⛔️erro ao configurar {nomefs}: {e}")
					else:
						print(f"⛔️erro: {e}")
						quit()
				if debug: print(f"✅ montagem e configuração de {nomefs} concluida")
		
			# ✅ MANTÉM a lógica original de inicialização do hardware
			if debug: print(f"⚙️ servicos da distro: {len(services)}")
			service_errors = 0
			for i, nomes in enumerate(services):
				with open("./code/" + nomes, "r") as code:
					if debug: print(f"📥 lendo {nomes}...")
					if nomes != "init.py":
						try:
							tmp_m.append((code.read(), nomes.replace(".py", "")+" service", SYSC))
						except Exception as e:
							if debug: print(f"⛔️ falha ao adicionar serviço '{nome}': {e}")
							service_errors += 1
							continue
						try:
							if serv_reset_m:
								if 'hw_instan' in globals():
									del hw_instan
						except NameError:
							if debug: print("⛔️hw_instan indisponivel, provalmente foi deletado antes da configuracao")
							service_erros = len(services)
							break
						try:
							hw_instan = hardware(tmp_m)
						except Exception as e:
							if debug: print(f"⛔️erro desconhecido: {e}")
							services_errors += 1
					else:
						try:
							hw_instan.memory = tmp_m
						except Exception as e:
							print(f"⛔️erro desconhecido: {e}")
							service_errors += 1
			total_sucesso = len(services) - service_errors
			if debug: print(f"⚙️ {total_sucesso} servicos adicionados com sucessso, {service_errors} deram erro")
		
			# 🆕 CORREÇÃO: Força a CPU a executar serviços pendentes
			if 'hw_instan' in globals():
				hw_instan.num = len(tmp_m) - len(services) - 1  # Volta para processar todos
				print(f"🎯 Executando {len(services)} serviços do sistema")
			self.servic = services
			self.ipccfg = ipc
		distro_cfg = True
		UFS = ufs

	



	def return_debug(self):
		return [hw_instan.ppn, tmp_m, hw_instan.num, hw_instan.mem_prot, self.servic, self.ipccfg]

def PHC(modo="auto", pid=None):
    """
    Process Health Check - Verifica a saúde dos processos
    
    Parâmetros:
    modo: "auto" (verifica todos), "single" (verifica apenas um PID)
    pid: Quando modo="single", o PID específico para verificar
    
    Retorna:
    dict: Relatório de saúde dos processos
    """
    global hw_instan
    
    if 'hw_instan' not in globals():
        return {"erro": "Sistema não inicializado"}
    
    relatorio = {
        "timestamp": time.time(),
        "processos_saudaveis": 0,
        "processos_problematicos": 0,
        "processos_travados": [],
        "processos_zumbis": [],
        "detalhes": {}
    }
    
    try:
        # Modo single - verifica apenas um processo
        if modo == "single" and pid is not None:
            if pid not in hw_instan.ppn:
                return {"erro": f"PID {pid} não encontrado"}
            
            processos_verificar = [pid]
        else:
            # Modo auto - verifica todos os processos
            processos_verificar = list(hw_instan.ppn.keys())
        
        for pid in processos_verificar:
            info = hw_instan.ppn[pid]
            nome = info[1]
            status = "saudavel"
            problemas = []
            
            # Verificação 1: Processo marcado para parar mas ainda ativo
            if pid in hw_instan.processos_parar:
                problemas.append("marcado_para_parar_mas_ainda_ativo")
                status = "problematico"
            
            # Verificação 2: Thread correspondente não está mais viva
            thread_index = next((i for i, t in enumerate(hw_instan.threads) 
                              if t.is_alive() and i == pid), None)
            if thread_index is None and pid not in hw_instan.processos_parar:
                problemas.append("thread_morta")
                status = "travado"
                relatorio["processos_travados"].append(pid)
            
            # Verificação 3: Processo sem atividade por muito tempo (simplificado)
            # (Em um sistema real, verificaria last_activity_time)
            
            # Verificação 4: PID muito alto pode indicar processo órfão
            if pid > 499 and "init" not in nome and "service" not in nome:
                problemas.append("possivel_zumbi")
                relatorio["processos_zumbis"].append(pid)
                status = "zumbi"
            
            # Atualizar relatório
            relatorio["detalhes"][pid] = {
                "nome": nome,
                "status": status,
                "problemas": problemas,
                "memoria_index": info[3] if len(info) > 3 else "N/A"
            }
            
            if status == "saudavel":
                relatorio["processos_saudaveis"] += 1
            else:
                relatorio["processos_problematicos"] += 1
        
        # Ação corretiva automática se solicitado
        if modo == "auto" and relatorio["processos_travados"]:
            if debug: 
                print(f"🔄 PHC: Encerrando {len(relatorio['processos_travados'])} processos travados")
            
            for pid_travado in relatorio["processos_travados"]:
                try:
                    matar_proc(pid_travado, False)
                    if debug: 
                        print(f"✅ PHC: Processo {pid_travado} encerrado")
                except Exception as e:
                    if debug: 
                        print(f"❌ PHC: Erro ao encerrar {pid_travado}: {e}")
        
        return relatorio
        
    except Exception as e:
        return {"erro": f"Falha no PHC: {str(e)}"}



phc_service = """
while True:
	time.sleep(10)
	relat = PHC('auto')
	existe, info = VED(None, 'init', 'name')
	if existe:
		IPC(info, f"relatorio_phc: {relat}", 0, "PHC Kernel Service")
	elif not existe:
		existe, info = VED(None, "sys_msg service", "name")
		if existe:
			IPC(info, f"relatorio_phc: {relat}", 0, "PHC Kernel Service")
		else:
			pass
	else:
		pass


"""

def IPC(destino, msg, assina_por_pid, assina_por_nome):
	global hw_instan
	hw_instan.ppn[destino][2] = [[assina_por_pid, assina_por_nome], msg]

def limpar_IPC(pid):
    global hw_instan
    if pid in hw_instan.ppn:
        hw_instan.ppn[pid][2] = []
        

def ler_IPC(pid):
	global hw_instan
	if len(hw_instan[pid][2]) == 2:
		lista_do_assinado = hw_instan.ppn[pid][2][0]
		msg = hw_instan.ppn[pid][2][1]
		return (True, lista_do_assinado, msg)
	else:
		return (False, None, None)

def installpkg(dev, pkg):
	pkg_exists = os.path.exists(f"../pkg/{pkg}.py")
	if shutil.which("git") and not pkg_exists:
		os.system(f'git clone https://github.com/{dev}/{pkg}-aurox-pkg.git ../pkg')
		if os.path.exists(f"../pkg/{pkg}.py"):
			return (True, "pacote instalado")
		else:
			return (False, "pacote não existe")
	else:
		if pkg_exists:
			return (False, "pacote já existe")
		else:
			return (False, "git não instalado")

def delpkg(pkg):
	os.remove(f"../pkg/{pkg}.py")

def listpkg():
	bruto = os.listdir('../pkg')
	for i, files in enumerate(bruto):
		bruto[i] = files.replace('.py', '')
	return bruto

def usepkg(pkg, comando="main", parametros=()):
	if comado == "main":
		pkg = __import__(pkg)
		funcao = getattr(pkg, comando)
		funcao(parametros)

def checkpkg(pkg):
	if os.path.exists(f"../pkg/{pkg}.py"):
		return True
	else:
		return False
		
boot_anim()
idle = True
idled = False
def pwroff_krnl(exit=True):
	global hw_instan
	global idle
	global UFS
	print("desligando...")
	time.sleep(0.4)
	print("encerrando processos...")
	time.sleep(0.3)
	
	# Encerrar todos os processos
	for pid, info in list(hw_instan.ppn.items()):
		if pid not in hw_instan.processos_parar:
			nome = info[1]  # pega o nome do processo
			matar_proc(pid, False)
			print(f"⚠️ {nome} encerrado")
			time.sleep(0.2)
	
	# Limpeza normal depois que todos os processos terminaram
	print("limpando ppn...")
	hw_instan.ppn.clear()
	print("✅ ppn limpado")
	time.sleep(0.2)
	
	print("limpando threads...")
	hw_instan.threads.clear()
	print("✅ limpado")
	time.sleep(0.2)
	
	print("bloqueando a memoria...")
	for i in range(500):
		hw_instan.mem_prot[i] = True
	print("✅ memoria bloqueada")
	if UFS:
		print("desmontando filesystems...")
		mounts = os.listdir("../mnt")
		for i, nomefs in enumerate(mounts):
			umnt(nomefs)
		print("✅ filesystems desmontados")
			
	print("finalizando...")
	idle = False
	if exit: quit()

def reboot():
	global distro_cfg, tmp_m, UFS, hw_instan, phc_service
	pwroff_krnl(exit=False)
	tmp_m = []
	distro_cfg = False
	UFS = None
	del hw_instan
	for i in range(500):
		hw_instan.mem_prot[i] = False
	tmp_m.append((phc_service, "PHC Kernel Service"))
	if os.path.exists('code/init.py'):
		try:
			with open("code/init.py", "r") as f:
				tmp_m.append((f.read(), "init"))
		except Exception:
			pass
			quit()
	else:
		codigos = os.listdir("code")
		for i, nomes in enumerate(codigos):
			with open(nome, "r") as f:
				try:
					tmp_m.append((f.read(), f"sys service {i}"))
				except Exception:
					pass
					print("erro, continuar mesmo assim?")
					a = input('(S/n): ')
					if a == "n" or a == "N":
						quit()
	globals()['hw_instan'] = hardware(tmp_m)
	

print(f"status_idle: {str(idle)}")
def initapp(app, reset_m, log, son=False, pidpai=None):
	global tmp_m, hw_instan
	
	# 🆕 CORREÇÃO: Encontrar o PRIMEIRO slot disponível
	slot_disponivel = None
	for i in range(len(hw_instan.mem_prot)):
		if not hw_instan.mem_prot[i]:  # Slot livre
			slot_disponivel = i
			break
	
	if slot_disponivel is None:
		if log: print("❌ Memória cheia - não é possível carregar app")
		return
	
	os.chdir("./apps/")
	with open(app + ".py", "r") as aplicativo:
		codigo = aplicativo.read()
		
		if reset_m:
			# Reset mas mantém a instância do hardware
			tmp_m = [(codigo, app, APPC)]
			hw_instan.memory = tmp_m
			hw_instan.num = 0
			hw_instan.ppn = {}
			hw_instan.processos_parar = {}
			hw_instan.mem_prot = [False] * 500
			hw_instan.old_sloot_f = []
			if log: print("🧹 Memória resetada - novo app carregado")
		else:
			# 🆕 CORREÇÃO: Usar o slot disponível encontrado
			memory_index = slot_disponivel
			
			# Garantir que tmp_m tenha espaço suficiente
			while len(tmp_m) <= memory_index:
				tmp_m.append((None, None, None))  # Preencher com placeholders
			
			# Colocar o app no slot livre
			tmp_m[memory_index] = (codigo, app, APPC)
			hw_instan.memory = tmp_m
			
			# 🆕 Forçar a CPU a processar a partir deste slot
			if memory_index <= hw_instan.num:
				hw_instan.num = memory_index - 1
			
			b = random.randint(1000, 9999)
			hw_instan.ppn[b] = [b, app, [], memory_index, False, None]
			
			if log: print(f"📱 App {app} carregado no slot {memory_index} (PID {b}) - aguardando execução pela CPU")
	
	os.chdir("..")

def initson_sys(codigo, nome, pidpai):
	global tmp_m, hw_instan
	
	# 🆕 CORREÇÃO: Encontrar o PRIMEIRO slot disponível
	slot_disponivel = None
	for i in range(len(hw_instan.mem_prot)):
		if not hw_instan.mem_prot[i]:  # Slot livre
			slot_disponivel = i
			break
	
	# ✅ CORREÇÃO CRÍTICA: Verificar se encontrou slot
	if slot_disponivel is None:
		if debug: print("❌ Memória cheia - não é possível criar processo filho")
		return False
	
	memory_index = slot_disponivel
		
	# Garantir que tmp_m tenha espaço suficiente
	while len(tmp_m) <= memory_index:
		tmp_m.append((None, None, None))  # Preencher com placeholders
		
	# Colocar o app no slot livre
	tmp_m[memory_index] = (codigo, nome, SYSC)
	hw_instan.memory = tmp_m
		
	# 🆕 Forçar a CPU a processar a partir deste slot
	if memory_index <= hw_instan.num:
		hw_instan.num = memory_index - 1
	
	if debug: print(f"✅ Código filho '{nome}' colocado no slot {memory_index} - aguardando CPU")
	
	# ✅ CORREÇÃO: Esperar CPU processar e depois atualizar relação pai-filho
	time.sleep(1)  # Dar tempo para CPU processar
	
	# 🆕 ENCONTRAR o PID real que a CPU atribuiu ao FILHO
	pid_filho_real = None
	for pid, info in hw_instan.ppn.items():
		if len(info) > 3 and info[3] == memory_index:  # Encontrou pelo memory_index
			pid_filho_real = pid
			break
	
	# 🆕 ENCONTRAR o PID real que a CPU atribuiu ao PAI
	pid_pai_real = None
	for pid, info in hw_instan.ppn.items():
		if info[1] == "teste2":  # ✅ Encontrar pelo nome do pai
			pid_pai_real = pid
			break
	
	if pid_filho_real and pid_pai_real:
		# ✅ ATUALIZAR relação pai-filho com PIDs REAIS
		hw_instan.ppn[pid_filho_real][4] = True       # is_son = True
		hw_instan.ppn[pid_filho_real][5] = pid_pai_real  # pidpai = PID REAL
		
		if debug: print(f"✅ Processo filho '{nome}' criado (PID {pid_filho_real}) para pai REAL {pid_pai_real}")
		return True
	else:
		if debug: print(f"❌ Não encontrou PIDs reais: filho={pid_filho_real}, pai={pid_pai_real}")
		return False
		
def initson(codigo, nome, pidpai):
	global tmp_m, hw_instan
	
	# 🆕 CORREÇÃO: Encontrar o PRIMEIRO slot disponível
	slot_disponivel = None
	for i in range(len(hw_instan.mem_prot)):
		if not hw_instan.mem_prot[i]:  # Slot livre
			slot_disponivel = i
			break
	
	# ✅ CORREÇÃO CRÍTICA: Verificar se encontrou slot
	if slot_disponivel is None:
		if debug: print("❌ Memória cheia - não é possível criar processo filho")
		return False
	
	memory_index = slot_disponivel
		
	# Garantir que tmp_m tenha espaço suficiente
	while len(tmp_m) <= memory_index:
		tmp_m.append((None, None, None))  # Preencher com placeholders
		
	# Colocar o app no slot livre
	tmp_m[memory_index] = (codigo, nome, APPC)
	hw_instan.memory = tmp_m
		
	# 🆕 Forçar a CPU a processar a partir deste slot
	if memory_index <= hw_instan.num:
		hw_instan.num = memory_index - 1
	
	if debug: print(f"✅ Código filho '{nome}' colocado no slot {memory_index} - aguardando CPU")
	
	# ✅ CORREÇÃO: Esperar CPU processar e depois atualizar relação pai-filho
	time.sleep(1)  # Dar tempo para CPU processar
	
	# 🆕 ENCONTRAR o PID real que a CPU atribuiu ao FILHO
	pid_filho_real = None
	for pid, info in hw_instan.ppn.items():
		if len(info) > 3 and info[3] == memory_index:  # Encontrou pelo memory_index
			pid_filho_real = pid
			break
	
	# 🆕 ENCONTRAR o PID real que a CPU atribuiu ao PAI
	pid_pai_real = None
	for pid, info in hw_instan.ppn.items():
		if info[1] == "teste2":  # ✅ Encontrar pelo nome do pai
			pid_pai_real = pid
			break
	
	if pid_filho_real and pid_pai_real:
		# ✅ ATUALIZAR relação pai-filho com PIDs REAIS
		hw_instan.ppn[pid_filho_real][4] = True       # is_son = True
		hw_instan.ppn[pid_filho_real][5] = pid_pai_real  # pidpai = PID REAL
		
		if debug: print(f"✅ Processo filho '{nome}' criado (PID {pid_filho_real}) para pai REAL {pid_pai_real}")
		return True
	else:
		if debug: print(f"❌ Não encontrou PIDs reais: filho={pid_filho_real}, pai={pid_pai_real}")
		return False

def criar_processo_filho(pai, nome, codigo):
	initson(codigo, nome, pai)

def CPFS(pai, nome, codigo):
	initson_sys(codigo, nome, pai)
	

def configurar_fs(nomefs, tipo_conectar, onde, parametros=None):
	"""
	Conecta um filesystem montado a um destino real do sistema
	(hardware, diretório, código paralelo, rede, ou servidores).

	Parâmetros:
		nomefs: nome do filesystem montado (em /mnt)
		tipo_conectar: 'hardware', 'diretorio', 'codigo_paralelo', 'rede', 'servidorweb', 'servidor'
		onde: destino da conexão (path, dispositivo ou host)
		parametros: dicionário opcional com parâmetros específicos

	Retorna:
		True se configurado com sucesso, False caso contrário.
	"""
	if parametros is None:
		parametros = {}

	mount_point = os.path.join('../mnt', nomefs)
	if not os.path.exists(mount_point):
		print(f"⛔ Erro: Filesystem '{nomefs}' não está montado.")
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
		elif tipo_conectar == 'servidorweb':
			return _conectar_servidorweb(nomefs, onde, parametros, mount_point)
		elif tipo_conectar == 'servidor':
			return _conectar_servidor(nomefs, onde, parametros, mount_point)
		else:
			print(f"⛔ Tipo de conexão '{tipo_conectar}' não reconhecido.")
			return False
	except Exception as e:
		print(f"Erro ao configurar {nomefs}: {e}")
		return False

def _conectar_servidorweb(nomefs, host, parametros, mount_point):
	"""
	Cria um servidor web real no filesystem.
	"""
	print(f"🌐 Iniciando servidor web '{nomefs}' em {host}:{parametros.get('porta', 80)}")
	
	porta = parametros.get('porta', 80)
	protocolo = parametros.get('protocolo', 'http')
	www_dir = parametros.get('www_dir', mount_point)

	try:
		# Verificar se o diretório existe
		if not os.path.exists(www_dir):
			os.makedirs(www_dir, exist_ok=True)
			print(f"📁 Diretório {www_dir} criado")

		# Código do servidor web
		servidor_code = f"""
import http.server
import socketserver
import os
import threading
import time

class WebHandler(http.server.SimpleHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		self.directory = '{www_dir}'
		super().__init__(*args, directory=self.directory, **kwargs)
	
	def log_message(self, format, *args):
		print(f"🌐 {{self.client_address[0]}} - {{self.command}} {{self.path}} - {{format % args}}")

def run_web_server():
	try:
		os.chdir('{www_dir}')
		with socketserver.TCPServer(("", {porta}), WebHandler) as httpd:
			print(f"✅ Servidor web '{nomefs}' rodando em http://localhost:{porta}")
			print(f"📁 Diretório: {www_dir}")
			httpd.serve_forever()
	except Exception as e:
		print(f"❌ Erro no servidor web: {{e}}")

# Executa em thread separada
thread = threading.Thread(target=run_web_server, daemon=True)
thread.start()
"""
		
		# Executa o servidor
		exec(servidor_code, globals())
		
		# Cria arquivo de status
		status_file = os.path.join(mount_point, 'server.status')
		with open(status_file, 'w') as f:
			f.write(f"servidor_web: {nomefs}\n")
			f.write(f"host: {host}\n")
			f.write(f"porta: {porta}\n")
			f.write(f"protocolo: {protocolo}\n")
			f.write(f"www_dir: {www_dir}\n")
			f.write(f"status: ativo\n")

		print(f"✅ Servidor web '{nomefs}' rodando em http://{host}:{porta}")
		return True
		
	except Exception as e:
		print(f"⛔ Erro ao iniciar servidor web {nomefs}: {e}")
		return False

def _conectar_servidor(nomefs, host, parametros, mount_point):
	"""
	Cria um servidor genérico com serviços específicos.
	"""
	print(f"🖥️ Iniciando servidor '{nomefs}' em {host}:{parametros.get('porta', 8080)}")
	
	porta = parametros.get('porta', 8080)
	protocolo = parametros.get('protocolo', 'tcp')
	servidor_arquivos = parametros.get('servidor_arquivos')
	servidor_servicos = parametros.get('servidor_servicos', [])

	try:
		# Código base do servidor
		servidor_base = f"""
import socket
import threading
import os
import time

class GenericServer:
	def __init__(self, host='', port={porta}):
		self.host = host
		self.port = port
		self.running = True
		self.file_server = '{servidor_arquivos}' if '{servidor_arquivos}' else None
		self.services = {servidor_servicos}
	
	def handle_client(self, client_socket):
		try:
			request = client_socket.recv(1024).decode('utf-8')
			print(f"📨 Cliente conectado: {{request[:50]}}...")
			
			# Resposta básica
			response = "HTTP/1.1 200 OK\\r\\n\\r\\nServidor Aurox Generic Server"
			client_socket.send(response.encode('utf-8'))
			
		except Exception as e:
			print(f"Erro no cliente: {{e}}")
		finally:
			client_socket.close()
	
	def start(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((self.host, self.port))
		server_socket.listen(5)
		
		print(f"✅ Servidor genérico '{nomefs}' rodando em {{self.host}}:{{self.port}}")
		print(f"📁 File server: {{self.file_server}}")
		print(f"🔧 Serviços: {{self.services}}")
		
		while self.running:
			try:
				client_socket, addr = server_socket.accept()
				client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
				client_thread.start()
			except Exception as e:
				if self.running:
					print(f"Erro no servidor: {{e}}")

def run_generic_server():
	server = GenericServer()
	server.start()

# Executa em thread separada
thread = threading.Thread(target=run_generic_server, daemon=True)
	thread.start()
"""
		
		# Executa o servidor
		exec(servidor_base, globals())
		
		# Cria arquivo de status
		status_file = os.path.join(mount_point, 'generic_server.status')
		with open(status_file, 'w') as f:
			f.write(f"servidor: {nomefs}\n")
			f.write(f"host: {host}\n")
			f.write(f"porta: {porta}\n")
			f.write(f"protocolo: {protocolo}\n")
			f.write(f"servidor_arquivos: {servidor_arquivos}\n")
			f.write(f"servidor_servicos: {servidor_servicos}\n")
			f.write(f"status: ativo\n")

		print(f"✅ Servidor genérico '{nomefs}' rodando em {protocolo}://{host}:{porta}")
		return True
		
	except Exception as e:
		print(f"⛔ Erro ao iniciar servidor {nomefs}: {e}")
		return False


# Mantenha as funções matar_proc e listar_proc como estão, mas adicione:

def matar_proc(pid, log):
	try:
		if 'hw_instan' in globals():
			# ✅ CORREÇÃO: Guardar relação pai-filho ANTES de modificar ppn
			pai_original = None
			if pid in hw_instan.ppn:
				# Se este processo é filho, guardar quem é o pai
				info = hw_instan.ppn[pid]
				if len(info) > 5 and info[4]:  # É filho
					pai_original = info[5]  # Guardar PID do pai
			
			if debug: 
				print(f"🔍 matar_proc: PID={pid}, Pai_original={pai_original}")
				print(f"🔍 PPN atual: {list(hw_instan.ppn.keys())}")

			# 1. Marcar processo para parar
			hw_instan.processos_parar[pid] = True
			hw_instan.old_sloot_f.append(pid)
			
			# 2. ✅ CORREÇÃO: Matar processos filhos - usar PID REAL do processo atual
			filhos_para_matar = []
			for fp, info in list(hw_instan.ppn.items()):
				if len(info) > 5 and info[4] and info[5] == pid:  # Filho deste processo
					filhos_para_matar.append(fp)
			
			# Matar todos os filhos identificados
			for filho_pid in filhos_para_matar:
				if filho_pid in hw_instan.ppn:
					if log: print(f"🎯 Matando filho {filho_pid} do pai {pid}")
					matar_proc(filho_pid, log)
			
			# 3. Se este processo era filho, matar irmãos (filhos do mesmo pai)
			if pai_original:
				irmaos_para_matar = []
				for fp, info in list(hw_instan.ppn.items()):
					if len(info) > 5 and info[4] and info[5] == pai_original and fp != pid:
						irmaos_para_matar.append(fp)
				
				for irmao_pid in irmaos_para_matar:
					if irmao_pid in hw_instan.ppn:
						if log: print(f"🎯 Matando irmão {irmao_pid} (mesmo pai {pai_original})")
						matar_proc(irmao_pid, log)
			
			# 4. CORREÇÃO: Processos com PID >= 500 não usam slots de memória
			memory_index = None
			if pid in hw_instan.ppn:
				# Se for processo do sistema (PID baixo) - usa slot
				if pid <= 499:  
					memory_index = pid
				else:
					# Se for app (PID alto) - NÃO usa slot, é temporário
					if debug: print(f"📱 App {pid} é temporário - sem slot de memória")
					memory_index = None
			
			# 5. CORREÇÃO: Só mexer na memória se for processo do sistema
			if memory_index is not None and memory_index < 500:
				# Verifica se há outros processos no mesmo memory_index
				outros_processos = False
				for other_pid, other_info in hw_instan.ppn.items():
					if other_pid != pid and other_pid < 500 and other_pid == memory_index:
						outros_processos = True
						break
				
				# Só libera se for o ÚNICO processo do sistema no slot
				if not outros_processos:
					hw_instan.mem_prot[memory_index] = False
					if log: print(f"🧹 Slot {memory_index} liberado")
				else:
					if log: print(f"🔒 Slot {memory_index} mantido - outros processos usando")
			
			# 6. Dar tempo para parar e remover
			time.sleep(0.1)
			
			if pid in hw_instan.ppn:
				nome_processo = hw_instan.ppn[pid][1]
				del hw_instan.ppn[pid]
				if log: print(f"Processo {pid} ({nome_processo}) terminado")
				
			hw_instan.old_sloot_f.append(pid)
			
	except Exception as e:
		if log: print(f"Erro ao matar processo {pid}: {e}")

def listar_proc(printp):
    procs = []
    """Função para listar processos - versão atualizada"""
    try:
        if 'hw_instan' in globals() and hasattr(hw_instan, 'ppn'):
            processos = hw_instan.ppn
            if processos:
                if printp: print("Processos em execução:")
                for pid, info in processos.items():
                    # Mostra se o processo está marcado para parar
                    status = "🛑" if pid in getattr(hw_instan, 'processos_parar', {}) else ""
                    if pid <= 499:
                    	if printp: print(f"{status} PID: {pid}, Nome: {info[1]}")
                    	procs.append([pid, info[1]])
            else:
                if printp: print("Nenhum processo em execução")
                return None
        else:
            if printp: print("Sistema não inicializado")
            return None
    except Exception as e:
        if printp: print(f"Erro ao listar processos: {e}")
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

 

APPC = {
"__name__": __name__,
"VED": VED,
"matar_proc": matar_proc,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"criar_processo_filho": criar_processo_filho,
"__builtins__":  __builtins__,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg,
"os": os,
"time": time,
"shutil": shutil,
"import2": __import__,
"random": random,
'sys_pid': sys_pid
}

SYSC = {
'__name__': __name__,
"__builtins__": __builtins__,
"mnt": mnt,
"umnt": umnt,
"configurar_fs": configurar_fs,
"matar_proc": matar_proc,
"APPC": APPC,
"distro": distro,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"pwroff_krnl": pwroff_krnl,
"debug": debug,
"criar_processo_filho": criar_processo_filho,
"CPFS": CPFS,
"initapp": initapp,
"reboot": reboot,
"installpkg": installpkg,
"delpkg": delpkg,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg,
"os": os,
"sys": sys,
"time": time,
"shutil": shutil,
"random": random,
"import2": __import__,
"sys_pid": sys_pid
}

KRNLC = {
'__name__': __name__,
"__builtins__": __builtins__,
"VED": VED,
"mnt": mnt,
"umnt": umnt,
"configurar_fs": configurar_fs,
"matar_proc": matar_proc,
"distro": distro,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"pwroff_krnl": pwroff_krnl,
"debug": debug,
"CPFS": CPFS,
"initapp": initapp,
'PHC': PHC,
"reboot": reboot,
"installpkg": installpkg,
"delpkg": delpkg,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg,
"os": os,
"sys": sys,
"time": time,
"shutil": shutil,
"random": random,
"import2": __import__,
"sys_pid": sys_pid,
"VSP": VSP
}

class HWIW:
    def __init__(self, hw_instan):
        self._hw_instan = hw_instan
        
    @property
    def processos_parar(self):
        return self._hw_instan.processos_parar
        
    # 🔒 BLOQUEIA acesso a outros atributos
    def __getattr__(self, name):
        if name == 'processos_parar':
            return self._hw_instan.processos_parar
        raise AttributeError(f"Acesso restrito a hw_instan.{name}")




containers = {}

class hardware:
	def __init__(self, m):
		self.memory = m
		self.num = -1
		self.threads = []
		self.thread_code = {}
		self.procn = 0
		self.ppn = {}
		self.processos_parar = {}
		self.mem_prot = [False] * 500
		self.old_sloot_f = []
		self.verificacoes = 0
		
		cput = th.Thread(target=self.cpu)
		cput.start()
		if debug: print("✅ Thread cpu iniciada")
	
	def cpu(self):
		global containers
		if debug: print("🔧 Método cpu() executando")
		
		debug_ativo = True  # Controla debug apenas durante inicialização
		
		while idle:
			# Debug apenas durante boot ou a cada 50 verificações
			if debug and debug_ativo and self.verificacoes % 10 == 0:
				print(f"📝 Memória tem {len(self.memory)} aplicações:")
				for i, app in enumerate(self.memory):
					containers[i] = {}
					status = "✅" if i < len(self.mem_prot) and self.mem_prot[i] else "⏳"
					print(f"  {status} codigo {i}: {app[0][:40]}...")
			
			processos_executados = False
			
			for i in range(len(self.memory)):
				if len(list(filter(lambda x: x == True, self.mem_prot))) == 500:
					if debug and debug_ativo:
						debug_ativo = False
						print("✅ Todos os processos executados - debug silenciado")
					continue
				
				# Pular slots já protegidos (em execução)
				if self.mem_prot[i]:
					continue
					
				# Pular slots já processados 
				if i <= self.num:
					continue
				
				try:
					if debug and debug_ativo: 
						print(f"🎯 Processando item {i}")
						print(f"🧪 Compilando código {i}...")
					
					compile(self.memory[i][0], '<string>', 'exec')
					if debug and debug_ativo: print(f"✅ Compilação funcionou")
					
					def create_thread(pid):
						def thread_func():
							codigo_wrap = f"""
import time
_original_code = '''{self.memory[i][0].replace("'", "\\'")}'''

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

if {pid} in hw_instan.processos_parar:
	pass
"""
							try:
								globals()["hw_instan"] = hw_instan
								exec(codigo_wrap, {"hw_instan": HWIW(hw_instan), **self.memory[i][2], **containers[i]})
							except Exception as e:
								print(f"Erro no processo {pid}: {e}")
						return thread_func
					
					self.thread_code[self.procn] = self.memory[i][0]
					self.ppn[self.procn] = [self.procn, self.memory[i][1], [], i, False, None]  # 🆕 Adiciona memory_index
					thread = th.Thread(target=create_thread(self.procn))
					thread.start()
					self.procn +=1
					self.threads.append(thread)
					
					# 🆕 CORREÇÃO CRÍTICA: Só definir mem_prot como True DEPOIS que a thread foi criada com sucesso
					if debug: print(f"🎯 ATUALIZANDO mem_prot[{i}] = True (antes: {self.mem_prot[i]})")
					self.mem_prot[i] = True
					if debug: print(f"✅ mem_prot[{i}] = {self.mem_prot[i]} (depois) - Processo PID {self.procn-1} iniciado")
					
					if self.old_sloot_f and i in self.old_sloot_f:
						self.old_sloot_f.remove(i)
					
					if debug and debug_ativo: 
						print(f"✅ Thread codigo {i} iniciada como PID {self.procn-1}")
					
					self.num = i
					processos_executados = True
					
				except Exception as e:
					# 🆕 CORREÇÃO: Se houve erro, NÃO marcar mem_prot como True
					if debug and debug_ativo: 
						print(f"❌ Erro no item {i}: {e} - Slot {i} NÃO será marcado como protegido")
						import traceback
						traceback.print_exc()
			
			# Se não executou nenhum processo novo, silencia o debug
			if not processos_executados and debug_ativo:
				debug_ativo = False
				
			
			self.verificacoes += 1
			time.sleep(1)
				
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
	tmp_m.append((phc_service, "PHC Kernel Service", KRNLC))
	x = """while True:
	time.sleep(0.5)
	VSP"""

	tmp_m.append((x, "VSP Kernel Service", KRNLC))
	
	# tmp
	tmpd = os.getcwd() + "/system/tmp"
	os.environ['TMP'] = tmpd
	os.environ['TMPDIR'] = tmpd
	os.environ['TEMP'] = tmpd
	
	# listdirs
	root_ = os.listdir()
	system_code_ = os.listdir("./system/code")
	if debug: print(f"📁 {len(system_code_)} codigos do sistema foram encontrados")
	if "./system/modules" not in sys.path:
		sys.path.insert(0, "./system/modules")
	if "./pkg" not in sys.path:
		sys.path.insert(0, "./pkg")
	
	erro_no_tmp_m = 0
	existe_init = False
	if os.path.exists("system/code/init.py") and os.path.isfile("system/code/init.py"):
		if debug: print("📖 lendo init.py...")
		existe_init = True
		with open("system/code/init.py", "r") as initfile:
			try:
				try:
					tmp_m.append((initfile.read(), "init", SYSC))
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
					tmp_m.append((code.read(), f"sys service {i}", SYSC))
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
		if debug and not idled: print(f"debug: idle = {idle}")
		if not idle:
			if debug and not idled: print(f"debug: idle = {idle}")
			break
		time.sleep(3)
		if not idle:
			if debug and not idled: print(f"debug: idle = {idle}")
			break
		if not idle: print(f"isso não deveria aparacer em idle = False\ntipo: {type(idle)}")
		idled = True
		time.sleep(20)
	# fim do idle processo
	
	
def remover_shell():
    # Pega o diretório atual + /shell
    shell_path = os.path.join(os.getcwd(), "shell")
    
    # Remove do /etc/shells (CORRIGIDO: usar \\ ou /)
    os.system(f"sed -i '\\|{shell_path}|d' /etc/shells")
    
    if debug: print(f"Shell {shell_path} removido do /etc/shells")
    
    # Verifica se ainda está listado
    os.system(f"grep -n '{shell_path}' /etc/shells")
    


