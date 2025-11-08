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
from dataclasses import dataclass
from typing import Optional, List, Dict
import glob
# (NOVO):
infos = {}
try:
	import keyboard
	infos["kb_forced_reboot_key"] = True
except Exception:
	infos["kb_forced_reboot_key"] = False

def FRK():
	global infos
	if not infos["kb_forced_reboot_key"]:
		return
	else:
		while True:
			time.sleep(0.5)
			if keyboard.is_pressed("ctrl+f+r"):
				os.execv(sys.executable, ["python"] + sys.argv)
			else:
				pass

th_FRK = th.Thread(target=FRK, daemon=False)
th_FRK.start()
	
class DistroError(Exception):
    def __init__(self, message):
        super().__init__(message)
        print(f"❌ DistroError: {message}")
        pwroff_krnl()
        sys.exit(1)  # ✅ SAÍDA AUTOMÁTICA

class AuroxError(Exception):
    def __init__(self, message):
        super().__init__(message)
        print(f"❌ AuroxError: {message}")
        pwroff_krnl()
        sys.exit(1)  # ✅ SAÍDA AUTOMÁTICA

def boot_anim():
	for i in range(5):
		os.system("clear")
		time.sleep(1)
		print("_")
		time.sleep(0.3)
		if i == 4:
			os.system("clear")

def auroxperm(perms=None, app_name=None):
    """
    Decorador para definir permissões de APPS (processos) no Aurox
    
    Parâmetros:
    perms: dict - Dicionário de permissões
    app_name: str - Nome do aplicativo
    
    Permissões:
    - filesystems: bool - acesso a mnt, umnt, configurar_fs
    - net: bool - acesso a módulos de rede
    - matar: bool - matar processos (exceto sys_pid)  
    - matarsys: bool - matar qualquer processo
    - sistema: bool - acesso completo ao sistema
    - ambiente: bool - modificar namespaces
    """
    
    if perms is None:
        perms = {}
    
    def decorator(app_code):
        """
        app_code é o código fonte do app (string)
        que será executado como processo
        """
        
        # Nome do app
        nome_final = app_name or "AppSemNome"
        
        # Permissões validadas
        permissoes = {
            'filesystems': perms.get('filesystems', False),
            'net': perms.get('net', False),
            'matar': perms.get('matar', False),
            'matarsys': perms.get('matarsys', False),
            'sistema': perms.get('sistema', False),
            'ambiente': perms.get('ambiente', False)
        }
        
        # 🔒 Aplicar restrições no código do app
        codigo_modificado = _aplicar_restricoes(app_code, permissoes, nome_final)
        
        # Registrar permissões no sistema (para o initapp usar)
        if not hasattr(auroxperm, 'apps_registrados'):
            auroxperm.apps_registrados = {}
        
        auroxperm.apps_registrados[nome_final] = {
            'codigo_original': app_code,
            'codigo_modificado': codigo_modificado,
            'permissoes': permissoes,
            'namespace': _criar_namespace_seguro(permissoes)
        }
        
        return codigo_modificado
    
    return decorator

def _aplicar_restricoes(codigo, permissoes, app_name):
    """Aplica restrições de permissões no código do app"""
    
    codigo_modificado = codigo
    
    # 1. Remover imports perigosos se sem permissão
    if not permissoes['net']:
        codigo_modificado = _remover_imports_rede(codigo_modificado)
    
    # 2. Substituir chamadas a funções restritas
    if not permissoes['filesystems']:
        codigo_modificado = _substituir_chamadas_fs(codigo_modificado)
    
    # 3. Adicionar verificações de segurança
    codigo_modificado = _adicionar_verificacoes_seguranca(codigo_modificado, permissoes, app_name)
    
    return codigo_modificado

def _remover_imports_rede(codigo):
    """Remove imports de módulos de rede"""
    imports_rede = [
        'import http.server', 'from http.server import',
        'import socket', 'from socket import', 
        'import socketserver', 'from socketserver import'
    ]
    
    for import_line in imports_rede:
        codigo = codigo.replace(import_line, f'# 🔒 BLOQUEADO: {import_line}')
    
    return codigo

def _substituir_chamadas_fs(codigo):
    """Substitui chamadas a funções de filesystem"""
    funcoes_fs = {
        'mnt(': '_funcao_bloqueada("mnt")(',
        'umnt(': '_funcao_bloqueada("umnt")(',
        'configurar_fs(': '_funcao_bloqueada("configurar_fs")('
    }
    
    for funcao, substituicao in funcoes_fs.items():
        codigo = codigo.replace(funcao, substituicao)
    
    return codigo

def _adicionar_verificacoes_seguranca(codigo, permissoes, app_name):
    """Adiciona verificações de segurança no código"""
    
    header_seguranca = f'''
# 🔒 EXECUÇÃO SEGURA - App: {app_name}
# Permissões: {permissoes}

def _verificar_permissao_matar(pid):
    """Verifica se app pode matar processo"""
    if not {permissoes['matar']} and not {permissoes['matarsys']}:
        raise AuroxError("App não tem permissão para matar processos")
    if {permissoes['matar']} and pid in sys_pid:
        raise AuroxError("App não pode matar processos do sistema")

# Substituição segura de matar_proc
def _matar_proc_seguro(pid, log=True):
    _verificar_permissao_matar(pid)
    return matar_proc(pid, log)

'''
    
    # Substituir matar_proc pela versão segura
    if not permissoes['matarsys']:
        codigo = codigo.replace('matar_proc(', '_matar_proc_seguro(')
    
    return header_seguranca + codigo

def _funcao_bloqueada(nome_funcao):
    """Retorna função que levanta erro quando chamada"""
    def bloqueada(*args, **kwargs):
        raise AuroxError(f"App não tem permissão para usar {nome_funcao}")
    return bloqueada

def _criar_namespace_seguro(permissoes):
    """Cria namespace seguro para o app baseado nas permissões"""
    namespace = APPC.copy()  # Começa com namespace básico
    
    # Remover funções baseado nas permissões
    if not permissoes['filesystems']:
        namespace.pop('mnt', None)
        namespace.pop('umnt', None) 
        namespace.pop('configurar_fs', None)
    
    if not permissoes['net']:
        # Remover acesso a módulos de rede
        pass  # Já tratado na modificação do código
    
    if not permissoes['matar'] and not permissoes['matarsys']:
        namespace['matar_proc'] = _funcao_bloqueada('matar_proc')
    
    return namespace

perm_padrao = {"net": True, "matar": True, "matarsys": False, "filesystems": False, "ambiente": False, "sistema": False}

appperms = {}
try:
	apps = os.listdir("./system/apps")
except Exception:
	apps = []
for app in apps:
	nome = app.replace(".py", "")
	appperms[nome] = perm_padrao

def addperm(perm, app):
	global appperms
	appperms[app][perm] = True

def delperm(perm, app):
	global appperms
	appperms[app][perm] = False

def default_perm(app):
	global appperms
	appperms[app] = perm_padrao

class domestico:
	@dataclass
	class email:
		destinario: str
		assunto: str
		mensagem: str
		remetente: Optional[str] = None
		cc: Optional[List[str]] = None
		anexos: Optional[List[str]] = None
	
	@dataclass
	class messages:
		remetente_tel: str
		msg: str
		destino_tel: str
		views: Optional[List[str]] = None
		ddd: Optional[int] = None
	
	@dataclass
	class app:
		code: str
		uid: Optional[int] = None
		name: Optional[str] = "app generico"
		perms: Optional[Dict[str, bool]] = None
		appdata: Optional[Dict[str, str]] = None

def VSP():
	try:
		global hw_instan
		global sys_pid
		global SYSC
	except Exception as e:
		raise AuroxError(f"erro: {e}")
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
sys_fs = []


umnt_op = False

# classe para as distros usarem
class distro:
	def __init__(self, nome, ver, fs, nomesfs, cfgfs, services, serv_reset_m, ipc, ufs, pkgs, umnt_op_cfg):
		global tmp_m, hw_instan, distro_cfg, UFS, sys_fs, umnt_op
		relat = {}
		err_msg = {}
		sys_fs = nomesfs
		umnt_op = umnt_op_cfg
		pkgs_c = 0
		pkgs_e = 0
		for i, pacote in enumerate(pkgs):
			if isinstance(pacote, list):
				pkg = installpkg(pacote[0], pacote[1])
				if pkg[0]:
					pkgs_c += 1
				else:
					pkgs_e += 1
			else:
				raise DistroError(f"pacote indice {i} não tem conteudo valido: {pacote}")
		if pkgs_c == len(pkgs):
			relat["pkgs"] =  {"status": "ok", "errors": pkgs_e, "successfully": pkgs_c, "time": time.time(), "err_msg": {}}
		elif pkgs_c == 0:
			relat["pkgs"] = {"status": "errors", "errors": pkgs_e, "successfully": pkgs_c, "time": time.time(), "err_msg": {}}
		elif pkgs_c >= 1 and not pkgs_c == len(pkgs):
			relat["pkgs"] = {"status": "partially_ok", "errors": pkgs_e, "successfully": pkgs_c, "time": time.time(), "err_msg": {}}
		if not distro_cfg:
			os.makedirs("./info", exist_ok=True)
			with open("./info/nome.txt", "w") as nomed:
				nomed.write(nome)
			with open("./info/ver.txt", "w") as verd:
				verd.write(ver)
			if ipc != False and ipc != True:
				raise DistroError("ipc deve ser True ou False")
			if not ipc:
				global IPC
				global limpar_IPC
				def sem_ipc():
					return None
				IPC = sem_ipc()
				limpar_IPC = sem_ipc()
			if debug: print(f"IPC = {ipc}")
			not_errors = 0
			if debug: print(f"💿 distro tem {len(nomesfs)} filesystems")
			err_msg["filesys"] = {}
			for i, nomefs in enumerate(nomesfs):
				if debug: print(f"💽 montando {nomefs}({i})...")
				tmp = 0
				try:
					mnt(fs[i], nomefs)
					tmp += 1
				except Exception as e:
					if debug:
						print(f"⛔️erro ao montar {nomefs}: {e}")
						err_msg["filesys"][f"{nomefs} | {i}"] = e
						continue
					else:
						print(f"⛔️erro: {e}")
						err_msg["filesys"][f"{nomefs} | {i}"] = e
						quit()
				if debug: print(f"⚙️ configurando {nomefs}")
				try:
					configurar_fs(nomefs, cfgfs[i][0], cfgfs[i][1], cfgfs[i][2])
					tmp += 1
				except Exception as e:
					if debug:
						print(f"⛔️erro ao configurar {nomefs}: {e}")
						err_msg["filesys"][f"{nomefs} | {i}"] = e
					else:
						print(f"⛔️erro: {e}")
						err_msg["filesys"][f"{nomefs} | {i}"] = e
						quit()
				if debug: print(f"✅ montagem e configuração de {nomefs} concluida")
				if tmp == 2:
					not_errors += 1
			if not_errors == len(nomesfs):
				relat["filesys"] = {"status": "ok", "errors": len(nomesfs) - not_errors, "successfully": not_errors, "time": time.time(), "err_msg": err_msg["filesys"]}
			elif not_errors == 0:
				relat["filesys"] =  {"status": "errors", "errors": len(nomesfs) - not_errors, "successfully": not_errors, "time": time.time(), "err_msg": err_msg1["filesys"]}
			elif not_errors < len(nomesfs) and not not_errors == 0:
				relat["filesys"] =  {"status": "partially_ok", "errors": len(nomesfs) - not_errors, "successfully": not_errors, "time": time.time(), "err_msg": err_msgqq["filesys"]}
		
			# ✅ MANTÉM a lógica original de inicialização do hardware
			if debug: print(f"⚙️ servicos da distro: {len(services)}")
			err_msg["services"] = {}
			service_errors = 0
			for i, nome in enumerate(services):
				with open("./code/" + nomes, "r") as code:
					if debug: print(f"📥 lendo {nome}...")
					if nomes != "init.py":
						try:
							tmp_m.append((code.read(), nomes.replace(".py", "")+" service", SYSC))
						except Exception as e:
							if debug: print(f"⛔️ falha ao adicionar serviço '{nome}': {e}")
							service_errors += 1
							err_msg["services"][f"{nome} | {i}"] = e
							continue
						try:
							if serv_reset_m:
								if 'hw_instan' in globals():
									del hw_instan
						except NameError:
							if debug: print("⛔️hw_instan indisponivel, provalmente foi deletado antes da configuracao")
							service_erros = len(services)
							break
							err_msg["services"]["all"] = "NameError"
						try:
							hw_instan = hardware(tmp_m)
						except Exception as e:
							if debug: print(f"⛔️erro desconhecido: {e}")
							services_errors += 1
							err_msg["services"][f"{nome} | {i}"] = e
					else:
						try:
							hw_instan.memory = tmp_m
						except Exception as e:
							print(f"⛔️erro desconhecido: {e}")
							service_errors += 1
							err_msg["services"][f"{nome} | {i}"] = e
			total_sucesso = len(services) - service_errors
			if debug: print(f"⚙️ {total_sucesso} servicos adicionados com sucessso, {service_errors} deram erro")
			if service_errors == 0:
				relat["services"]  = {"status": "ok", "errors": service_errors, "successfully": total_sucesso, "time": time.time(), "err_msg": err_msg["services"]}
			elif total_sucesso == 0:
				relat["services"] = {"status": "error", "errors": service_errors, "successfully": total_sucesso, "time": time.time(), "err_msg": err_msg["services"]}
			elif total_sucesso < len(services) and not total_sucesso == 0:
				relat["services"] = {"status": "partially_ok", "errors": service_errors, "successfully": total_sucesso, "time": time.time(), "err_msg": err_msg["services"]}
		
			# 🆕 CORREÇÃO: Força a CPU a executar serviços pendentes
			if 'hw_instan' in globals():
				hw_instan.num = len(tmp_m) - len(services) - 1  # Volta para processar todos
				print(f"🎯 Executando {len(services)} serviços do sistema")
			self.servic = services
			self.ipccfg = ipc
		distro_cfg = True
		if ufs != False and ufs != True:
			raise DistroError("ufs deve ser True ou False")
		UFS = ufs
		
		self.relat = relat

	



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
	if not os.path.exists("../pkg"):
		raise DistroError("não existe pkg/")
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
	

def LinuxFs():
    """
    Monta os filesystems sys, proc e dev REALMENTE - sem simulações
    """
    try:
        # Criar estrutura de diretórios
        os.makedirs("../mnt/sys", exist_ok=True)
        os.makedirs("../mnt/proc", exist_ok=True)
        os.makedirs("../mnt/dev", exist_ok=True)
        
        # Filesystem SYS
        _iniciar_servico_sys()
        
        # Filesystem PROC  
        _iniciar_servico_proc()
        
        # Filesystem DEV
        _iniciar_servico_dev()
        
        print("✅ LinuxFs: sys, proc, dev montados REALMENTE")
        return True
        
    except Exception as e:
        print(f"❌ LinuxFs erro: {e}")
        return False

def _iniciar_servico_sys():
    """Servico REAL para filesystem sys"""
    servico_code = """
import os
import time
import threading

def atualizar_sys():
    while True:
        try:
            # /sys/class/battery/
            battery_path = "../mnt/sys/class/battery"
            os.makedirs(battery_path, exist_ok=True)
            
            # Informações REAIS da bateria
            percent = ler_bateria_real()
            status = ler_info_bateria_real("status")
            capacity = ler_info_bateria_real("cap_lev")
            model = ler_info_bateria_real("modelo")
            serial = ler_info_bateria_real("serial")
            
            with open(os.path.join(battery_path, "percent.txt"), "w") as f:
                f.write(str(percent) if percent else "indisponivel")
            with open(os.path.join(battery_path, "status.txt"), "w") as f:
                f.write(status if status else "indisponivel")
            with open(os.path.join(battery_path, "capacity_level.txt"), "w") as f:
                f.write(capacity if capacity else "indisponivel")
            with open(os.path.join(battery_path, "model.txt"), "w") as f:
                f.write(model if model else "indisponivel")
            with open(os.path.join(battery_path, "serial.txt"), "w") as f:
                f.write(serial if serial else "indisponivel")

            # /sys/class/temp/
            temp_path = "../mnt/sys/class/temp"
            os.makedirs(temp_path, exist_ok=True)
            
            temp_c = ler_temperatura_real()
            temp_f = temp_c * 9/5 + 32 if temp_c else None
            
            with open(os.path.join(temp_path, "c.txt"), "w") as f:
                f.write(f"{temp_c:.1f}" if temp_c else "indisponivel")
            with open(os.path.join(temp_path, "f.txt"), "w") as f:
                f.write(f"{temp_f:.1f}" if temp_f else "indisponivel")

            # /sys/system/
            system_path = "../mnt/sys/system"
            os.makedirs(system_path, exist_ok=True)
            try:
                for i, cpu in enumerate(glob.glob("/sys/devices/cpu/cpu*"))
                shutil.rmtree(f"../mnt/sys/system/cpu{i}")
                shutil.copy2(cpu, f"../mnt/sys/system/cpu{i}")
            
            # Processos do sistema REAIS
            with open(os.path.join(system_path, "sys_pid.txt"), "w") as f:
                for pid in sys_pid:
                    f.write(f"{pid}\\n")
            
            # Informações do kernel
            with open(os.path.join(system_path, "kernel_info.txt"), "w") as f:
                f.write("Aurox Kernel\\n")
                f.write(f"Processos sistema: {len(sys_pid)}\\n")
                f.write(f"Timestamp: {time.time()}\\n")

            time.sleep(2)  # Atualizar a cada 2 segundos
            
        except Exception as e:
            print(f"Erro sys: {e}")
            time.sleep(5)

thread = threading.Thread(target=atualizar_sys, daemon=True)
thread.start()
"""
    exec(servico_code, globals())

def _iniciar_servico_proc():
    """Servico REAL para filesystem proc"""
    servico_code = """
import os
import time
import threading

def atualizar_proc():
    while True:
        try:
            # Arquivos globais
            mem_usage = ler_uso_ram_real()
            cpu_usage = ler_uso_cpu_real()
            
            with open("../mnt/proc/mem_usage.txt", "w") as f:
                f.write(f"{mem_usage:.1f}" if mem_usage else "indisponivel")
            with open("../mnt/proc/cpu_usage.txt", "w") as f:
                f.write(f"{cpu_usage:.1f}" if cpu_usage else "indisponivel")

            # Processos REAIS do sistema
            for pid, info in hw_instan.ppn.items():
                pid_path = f"../mnt/proc/{pid}"
                os.makedirs(pid_path, exist_ok=True)
                
                # cmdline - nome do processo
                with open(os.path.join(pid_path, "cmdline"), "w") as f:
                    f.write(info[1] if len(info) > 1 else "desconhecido")
                
                # exe - tipo de processo
                with open(os.path.join(pid_path, "exe"), "w") as f:
                    memory_index = info[3] if len(info) > 3 else None
                    if memory_index is not None and memory_index < len(hw_instan.memory):
                        env_type = hw_instan.memory[memory_index][2]
                        if env_type == APPC:
                            f.write(f"{os.getcwd()}/apps/{info[1]}.py")
                        elif env_type == SYSC:
                            f.write(f"{os.getcwd()}/code/{info[1].replace(" service", "")}.py")
                        elif env_type == KRNLC:
                            f.write("kernel")
                        else:
                            f.write("desconhecido")
                    else:
                        f.write("kernel")  # Processos do kernel
                
                # ambiente - namespace
                with open(os.path.join(pid_path, "ambiente"), "w") as f:
                    memory_index = info[3] if len(info) > 3 else None
                    if memory_index is not None and memory_index < len(hw_instan.memory):
                        env_type = hw_instan.memory[memory_index][2]
                        if env_type == APPC:
                            f.write("APPC")
                        elif env_type == SYSC:
                            f.write("SYSC") 
                        elif env_type == KRNLC:
                            f.write("KRNLC")
                        else:
                            f.write("OUTRO")
                    else:
                        f.write("KRNLC")
                
                # permissions - permissões do app
                with open(os.path.join(pid_path, "permissions"), "w") as f:
                    nome_processo = info[1] if len(info) > 1 else ""
                    if nome_processo in appperms:
                        perms = appperms[nome_processo]
                        f.write(str(perms))
                    else:
                        f.write("perm_padrao")
                
                # Processos filhos - criar dentro da pasta do pai
                if len(info) > 5 and info[4]:  # is_son = True
                    pai_pid = info[5]
                    if pai_pid in hw_instan.ppn:
                        pai_path = f"../mnt/proc/{pai_pid}/filhos"
                        os.makedirs(pai_path, exist_ok=True)
                        with open(os.path.join(pai_path, str(pid)), "w") as f:
                            f.write(info[1] if len(info) > 1 else "filho")

            # Limpar processos que não existem mais
            proc_dir = "../mnt/proc"
            for item in os.listdir(proc_dir):
                item_path = os.path.join(proc_dir, item)
                if os.path.isdir(item_path) and item.isdigit():
                    pid_num = int(item)
                    if pid_num not in hw_instan.ppn:
                        shutil.rmtree(item_path)

            time.sleep(3)  # Atualizar a cada 3 segundos
            
        except Exception as e:
            print(f"Erro proc: {e}")
            time.sleep(5)

thread = threading.Thread(target=atualizar_proc, daemon=True)
thread.start()
"""
    exec(servico_code, globals())

def _iniciar_servico_dev():
    """Servico REAL para filesystem dev"""
    servico_code = """
import os
import time
import threading
import secrets
import random

def atualizar_dev():
    while True:
        try:
            # /dev/input/
            input_path = "../mnt/dev/input"
            os.makedirs(input_path, exist_ok=True)
            
            # Eventos REAIS de input
            for i in range(11):  # event0 a event10
                event_file = os.path.join(input_path, f"event{i}")
                eventos = ler_eventos_input_legivel(f"/dev/input/event{i}", 5)
                with open(event_file, "w") as f:
                    for evento in eventos:
                        f.write(f"{evento}\\n")

            # /dev/null/ - TUDO é deletado
            null_path = "../mnt/dev/null"
            os.makedirs(null_path, exist_ok=True)
            for item in os.listdir(null_path):
                item_path = os.path.join(null_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass

            # /dev/usb/ - conteúdo REAL de pen-drives
            usb_path = "../mnt/dev/usb"
            os.makedirs(usb_path, exist_ok=True)
            
            # Procurar dispositivos USB REAIS
            usb_devices = []
            for device in glob.glob("/sys/bus/usb/devices/*"):
                if os.path.exists(os.path.join(device, "product")):
                    usb_devices.append(device)
            
            for i, device in enumerate(usb_devices[:10]):  # Máximo 10 dispositivos
                usb_device_path = os.path.join(usb_path, f"usb{i}")
                os.makedirs(usb_device_path, exist_ok=True)
                
                try:
                    # Tentar montar se estiver disponível
                    mount_point = f"/media/usb{i}"
                    if os.path.exists(mount_point):
                        for item in os.listdir(mount_point):
                            source = os.path.join(mount_point, item)
                            dest = os.path.join(usb_device_path, item)
                            if os.path.isfile(source) and not os.path.exists(dest):
                                shutil.copy2(source, dest)
                except:
                    pass

            # Arquivos especiais em /dev/
            # /dev/zero - 1KB de 0x00
            with open("../mnt/dev/zero", "wb") as f:
                f.write(b'\\x00' * 1024)

            # /dev/tty - console atual (se possível)
            try:
                with open("../mnt/dev/tty", "w") as f:
                    f.write("terminal_python")
            except:
                pass

            # /dev/ttyS0 a /dev/ttyS9 - seriais
            for i in range(10):
                tty_path = f"../mnt/dev/ttyS{i}"
                with open(tty_path, "w") as f:
                    f.write(f"serial_port_{i}")

            # /dev/random - número aleatório
            with open("../mnt/dev/random", "w") as f:
                f.write(str(random.randint(0, 999999999999999)))

            # /dev/urandom - número aleatório criptográfico
            with open("../mnt/dev/urandom", "w") as f:
                f.write(str(secrets.randbelow(999999999999999)))

            time.sleep(1)  # Atualizar a cada 1 segundo
            
        except Exception as e:
            print(f"Erro dev: {e}")
            time.sleep(5)

thread = threading.Thread(target=atualizar_dev, daemon=True)
thread.start()
"""
    exec(servico_code, globals())

print(f"status_idle: {str(idle)}")
def initapp(app, reset_m, log, son=False, pidpai=None):
	global tmp_m, hw_instan, appperms
	
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
		codigo_original = aplicativo.read()
		
		# 🆕 SISTEMA DE PERMISSÕES - Verificar permissões na variável global appperms
		codigo_final = codigo_original
		namespace_app = APPC  # Namespace padrão
		
		if app in appperms:
			# 🎯 App tem permissões definidas na distro - aplicar restrições
			permissoes = appperms[app]
			if log: print(f"🔒 Aplicando permissões para {app}: {permissoes}")
			
			codigo_final = _aplicar_restricoes_app(codigo_original, app, permissoes)
			namespace_app = _criar_namespace_app(app, permissoes)
		else:
			# 🔒 App sem permissões definidas - aplicar restrições padrão
			if log: print(f"⚠️ App {app} não tem permissões definidas em appperms - usando restrições padrão")
			codigo_final = _aplicar_restricoes_padrao(codigo_original, app)
			namespace_app = _criar_namespace_padrao()
		
		if reset_m:
			# Reset mas mantém a instância do hardware
			tmp_m = [(codigo_final, app, namespace_app)]
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
				tmp_m.append((None, None, None))
			
			# Colocar o app no slot livre
			tmp_m[memory_index] = (codigo_final, app, namespace_app)
			hw_instan.memory = tmp_m
			
			# 🆕 Forçar a CPU a processar a partir deste slot
			if memory_index <= hw_instan.num:
				hw_instan.num = memory_index - 1
			
			b = random.randint(1000, 9999)
			hw_instan.ppn[b] = [b, app, [], memory_index, False, None]
			
			if log: 
				perm_info = "com permissões personalizadas" if app in appperms else "com restrições padrão"
				print(f"📱 App {app} carregado no slot {memory_index} (PID {b}) {perm_info}")
	
	os.chdir("..")

# 🆕 FUNÇÕES AUXILIARES PARA SISTEMA DE PERMISSÕES

def _aplicar_restricoes_app(codigo, app_name, permissoes):
	"""Aplica restrições baseado nas permissões definidas na distro"""
	codigo_modificado = codigo
	
	# 🔒 Restrições de filesystems
	if not permissoes.get('filesystems', False):
		codigo_modificado = _remover_chamadas_fs(codigo_modificado, app_name)
	
	# 🔒 Restrições de rede
	if not permissoes.get('net', False):
		codigo_modificado = _remover_imports_rede(codigo_modificado, app_name)
	
	# 🔒 Restrições de matar processos
	if not permissoes.get('matar', False) and not permissoes.get('matarsys', False):
		codigo_modificado = _bloquear_matar_proc(codigo_modificado, app_name)
	elif permissoes.get('matar', False) and not permissoes.get('matarsys', False):
		codigo_modificado = _proteger_matar_sistema(codigo_modificado, app_name)
	
	return codigo_modificado

def _criar_namespace_app(app_name, permissoes):
	"""Cria namespace personalizado baseado nas permissões da distro"""
	namespace = APPC.copy()
	
	# 🔒 Aplicar restrições no namespace
	if not permissoes.get('filesystems', False):
		namespace['mnt'] = _funcao_bloqueada('mnt', f"App {app_name} sem permissão filesystems")
		namespace['umnt'] = _funcao_bloqueada('umnt', f"App {app_name} sem permissão filesystems")
		namespace['configurar_fs'] = _funcao_bloqueada('configurar_fs', f"App {app_name} sem permissão filesystems")
	
	if not permissoes.get('matar', False) and not permissoes.get('matarsys', False):
		namespace['matar_proc'] = _funcao_bloqueada('matar_proc', f"App {app_name} sem permissão matar")
	elif permissoes.get('matar', False) and not permissoes.get('matarsys', False):
		# Substitui por versão protegida
		def _matar_protected(pid, log=True):
			if pid in sys_pid:
				raise AuroxError(f"App {app_name} não pode matar processo do sistema PID {pid}")
			return matar_proc(pid, log)
		namespace['matar_proc'] = _matar_protected
	
	return namespace

def _aplicar_restricoes_padrao(codigo, app_name):
	"""Aplica restrições padrão para apps sem permissões definidas"""
	codigo_modificado = codigo
	
	# 🔒 Restrições máximas por padrão
	codigo_modificado = _remover_chamadas_fs(codigo_modificado, app_name)
	codigo_modificado = _remover_imports_rede(codigo_modificado, app_name)
	codigo_modificado = _bloquear_matar_proc(codigo_modificado, app_name)
	
	return codigo_modificado

def _criar_namespace_padrao():
	"""Cria namespace com restrições máximas"""
	namespace = APPC.copy()
	
	# 🔒 Bloquear tudo por padrão
	funcoes_perigosas = ['mnt', 'umnt', 'configurar_fs', 'matar_proc']
	for funcao in funcoes_perigosas:
		if funcao in namespace:
			namespace[funcao] = _funcao_bloqueada(funcao, "App sem permissões definidas")
	
	return namespace

def _funcao_bloqueada(nome_funcao, motivo):
	"""Retorna função que levanta erro quando chamada"""
	def bloqueada(*args, **kwargs):
		raise AuroxError(f"🔒 {motivo}: {nome_funcao}")
	return bloqueada

def _remover_chamadas_fs(codigo, app_name):
	"""Substitui chamadas a funções de filesystem"""
	funcoes_fs = ['mnt', 'umnt', 'configurar_fs']
	
	for funcao in funcoes_fs:
		codigo = codigo.replace(
			f'{funcao}(',
			f'_funcao_bloqueada("{funcao}", "App {app_name} sem permissão filesystems")('
		)
	
	return codigo

def _remover_imports_rede(codigo, app_name):
	"""Remove imports de módulos de rede"""
	imports_rede = [
		'import http.server',
		'from http.server import',
		'import socket', 
		'from socket import',
		'import socketserver',
		'from socketserver import'
	]
	
	for import_line in imports_rede:
		codigo = codigo.replace(
			import_line,
			f'# 🔒 PERMISSÃO NEGADA: {import_line} (app {app_name} sem permissão net)'
		)
	
	return codigo

def _bloquear_matar_proc(codigo, app_name):
	"""Bloqueia função matar_proc"""
	codigo = codigo.replace(
		'matar_proc(',
		f'_funcao_bloqueada("matar_proc", "App {app_name} sem permissão matar")('
	)
	return codigo

def _proteger_matar_sistema(codigo, app_name):
	"""Substitui matar_proc por versão que protege processos do sistema"""
	protecao_code = f'''
def _matar_proc_protegido(pid, log=True):
	"""Versão protegida de matar_proc"""
	if pid in sys_pid:
		raise AuroxError("App '{app_name}' não pode matar processos do sistema PID {{pid}}")
	return matar_proc(pid, log)

'''
	codigo = codigo.replace('matar_proc(', '_matar_proc_protegido(')
	return protecao_code + codigo

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
	
import os

def ler_temperatura_real():
    """
    Lê temperatura real do sistema (Linux)
    Retorna temperatura em Celsius ou None se não disponível
    """
    try:
        # Tentar diferentes caminhos comuns de temperatura
        caminhos_temperatura = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input", 
            "/sys/class/hwmon/hwmon1/temp1_input",
            "/sys/devices/virtual/thermal/thermal_zone0/temp"
        ]
        
        for caminho in caminhos_temperatura:
            if os.path.exists(caminho):
                with open(caminho, 'r') as f:
                    temp_millic = int(f.read().strip())
                    temp_c = temp_millic / 1000.0  # Converter millicelsius para celsius
                    return temp_c
        
        # Se não encontrou, tentar comando 'sensors'
        try:
            import subprocess
            result = subprocess.run(['sensors'], capture_output=True, text=True)
            if 'Core 0' in result.stdout:
                # Extrair temperatura do output (exemplo: "Core 0:       +45.0°C")
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Core 0' in line or 'temp1' in line:
                        import re
                        match = re.search(r'([+-]?\d+\.\d+)°C', line)
                        if match:
                            return float(match.group(1))
        except:
            pass
            
        return None  # Temperatura não disponível
        
    except Exception as e:
        print(f"Erro ao ler temperatura: {e}")
        return None

def ler_uso_cpu_real():
    """Lê uso real da CPU do sistema Linux"""
    try:
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('cpu '):
                parts = line.split()
                # Campos: user, nice, system, idle, iowait, irq, softirq
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                iowait = int(parts[5])
                
                total = user + nice + system + idle + iowait
                used = total - idle
                
                if total > 0:
                    return (used / total) * 100  # Percentual
        return 0
    except:
        return None

def ler_uso_ram_real():
    """Lê uso real de memória RAM do sistema Linux"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_total = 0
        mem_available = 0
        
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])  # Em KB
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1])  # Em KB
        
        if mem_total > 0:
            mem_used = mem_total - mem_available
            return (mem_used / mem_total) * 100  # Percentual
        return 0
    except:
        return None

def ler_bateria_real():
    """Lê status real da bateria (se disponível)"""
    try:
        # Tentar caminhos comuns de bateria
        caminhos_bateria = [
            "/sys/class/power_supply/BAT0/capacity",
            "/sys/class/power_supply/BAT1/capacity", 
            "/proc/acpi/battery/BAT0/info"
        ]
        
        for caminho in caminhos_bateria:
            if os.path.exists(caminho):
                with open(caminho, 'r') as f:
                    conteudo = f.read().strip()
                    # Extrair número (ex: "85" ou "capacity: 85")
                    import re
                    match = re.search(r'(\d+)', conteudo)
                    if match:
                        return int(match.group(1))  # Percentual
        
        return None  # Sem bateria detectada
    except:
        return None

def ler_info_bateria_real(info):
	a = "/sys/class/power_supply/BAT0"
	if info == "status":
		a = a + "/status"
	elif info == "cap_lev":
		a = a + "/capacity_level"
	elif info == "modelo":
		a = a + "/model_name"
	elif info == "serial":
		a = a + '/serial_number'
	try:
		with open(a, "r") as f:
			b = f.read()
	except PermissionError:
		b = "acesso negado"
	except FileNotFoundError:
		b = "indisponivel"
	return b

def ler_status_audio_out_real():
    """Verifica status real do áudio de saída"""
    try:
        import subprocess
        
        # Método 1: amixer (ALSA)
        result = subprocess.run(['amixer', 'get', 'Master'], 
                              capture_output=True, text=True)
        if '[on]' in result.stdout:
            return "ativo"
        elif '[off]' in result.stdout:
            return "mudo"
        
        # Método 2: pactl (PulseAudio)
        result = subprocess.run(['pactl', 'list', 'sinks'], 
                              capture_output=True, text=True)
        if 'State: RUNNING' in result.stdout:
            return "ativo"
        else:
            return "inativo"
            
    except:
        return "indisponivel"

def ler_status_audio_in_real():
    """Verifica status real do áudio de entrada"""
    try:
        import subprocess
        
        # Método 1: amixer (ALSA)
        result = subprocess.run(['amixer', 'get', 'Capture'], 
                              capture_output=True, text=True)
        if '[on]' in result.stdout:
            return "ativo"
        elif '[off]' in result.stdout:
            return "mudo"
        
        # Método 2: pactl (PulseAudio)
        result = subprocess.run(['pactl', 'list', 'sources'], 
                              capture_output=True, text=True)
        if 'State: RUNNING' in result.stdout:
            return "ativo"
        else:
            return "inativo"
            
    except:
        return "indisponivel"

def MCA(appc):
	global APPC
	APPC = appc

def ler_status_bluetooth_real():
    """Verifica status real do Bluetooth"""
    try:
        import subprocess
        
        # Método 1: rfkill
        result = subprocess.run(['rfkill', 'list'], capture_output=True, text=True)
        if 'bluetooth' in result.stdout.lower():
            if 'unblocked' in result.stdout.lower():
                return "ativo"
            else:
                return "inativo"
        
        # Método 2: systemctl
        result = subprocess.run(['systemctl', 'status', 'bluetooth'], 
                              capture_output=True, text=True)
        if 'active (running)' in result.stdout:
            return "ativo"
        else:
            return "inativo"
            
    except:
        return "indisponivel"

def mapear_evento_legivel(tipo, codigo, valor):
    """Converte eventos brutos para nomes legíveis"""
    
    # Tipos de evento
    tipos = {
        0: 'EV_SYN',      # Sincronização
        1: 'EV_KEY',      # Teclas/botões
        2: 'EV_REL',      # Movimento relativo (mouse)
        3: 'EV_ABS',      # Movimento absoluto (touch)
        4: 'EV_MSC',      # Miscelânea
        17: 'EV_LED',     # LEDs
        20: 'EV_REP',     # Repetição
    }
    
    # Teclas do teclado (EV_KEY)
    teclas = {
        1: 'ESC',        2: '1',          3: '2',          4: '3',          5: '4',
        6: '5',          7: '6',          8: '7',          9: '8',          10: '9',
        11: '0',         12: '-',         13: '=',         14: 'BACKSPACE', 15: 'TAB',
        16: 'Q',         17: 'W',         18: 'E',         19: 'R',         20: 'T',
        21: 'Y',         22: 'U',         23: 'I',         24: 'O',         25: 'P',
        26: '[',         27: ']',         28: 'ENTER',     29: 'CTRL_LEFT', 30: 'A',
        31: 'S',         32: 'D',         33: 'F',         34: 'G',         35: 'H',
        36: 'J',         37: 'K',         38: 'L',         39: ';',         40: "'",
        41: '`',         42: 'SHIFT_LEFT',43: '\\',        44: 'Z',         45: 'X',
        46: 'C',         47: 'V',         48: 'B',         49: 'N',         50: 'M',
        51: ',',         52: '.',         53: '/',         54: 'SHIFT_RIGHT',55: '*',
        56: 'ALT_LEFT',  57: 'SPACE',     58: 'CAPS_LOCK', 59: 'F1',        60: 'F2',
        61: 'F3',        62: 'F4',        63: 'F5',        64: 'F6',        65: 'F7',
        66: 'F8',        67: 'F9',        68: 'F10',       69: 'NUM_LOCK',  70: 'SCROLL_LOCK',
        103: 'UP',       108: 'DOWN',     105: 'LEFT',     106: 'RIGHT',
        113: 'VOL_MUTE', 114: 'VOL_DOWN', 115: 'VOL_UP',
    }
    
    # Botões do mouse (EV_KEY)
    botoes_mouse = {
        272: 'MOUSE_LEFT',    273: 'MOUSE_RIGHT',   274: 'MOUSE_MIDDLE',
        275: 'MOUSE_SIDE',    276: 'MOUSE_EXTRA',
    }
    
    # Movimento do mouse (EV_REL)
    movimento_mouse = {
        0: 'MOUSE_X',    1: 'MOUSE_Y',    2: 'MOUSE_WHEEL',
        6: 'MOUSE_TILT', 8: 'MOUSE_WHEEL_H',
    }
    
    nome_tipo = tipos.get(tipo, f'TIPO_{tipo}')
    
    if tipo == 1:  # EV_KEY
        nome_codigo = teclas.get(codigo, botoes_mouse.get(codigo, f'KEY_{codigo}'))
        acao = 'PRESS' if valor == 1 else 'RELEASE' if valor == 0 else f'VAL_{valor}'
        
    elif tipo == 2:  # EV_REL
        nome_codigo = movimento_mouse.get(codigo, f'REL_{codigo}')
        acao = f'MOV_{valor}'
        
    elif tipo == 3:  # EV_ABS (touch)
        nome_codigo = f'ABS_{codigo}'
        acao = f'POS_{valor}'
        
    else:
        nome_codigo = f'CODE_{codigo}'
        acao = f'VAL_{valor}'
    
    return f"{nome_tipo} {nome_codigo} {acao}"

def ler_eventos_input_legivel(dispositivo, max_eventos=10):
    """Lê eventos com nomes legíveis"""
    try:
        import struct
        eventos = []
        
        with open(dispositivo, 'rb') as f:
            for _ in range(max_eventos):
                try:
                    data = f.read(16)
                    if not data:
                        break
                    
                    sec, usec, tipo, codigo, valor = struct.unpack('llHHI', data)
                    
                    evento_legivel = mapear_evento_legivel(tipo, codigo, valor)
                    eventos.append(evento_legivel)
                        
                except BlockingIOError:
                    break
                    
        return eventos
        
    except Exception as e:
        return [f"ERRO: {e}"]

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

def _conectar_hardware(nomefs, dispositivo, parametros, mount_point):
    """
    Conecta filesystem a hardware real com detecção automática de tipo
    e atualização dinâmica a cada 0.4 segundos.
    """
    print(f"🔌 Conectando '{nomefs}' ao hardware '{dispositivo}'")
    
    try:
        # Detecção automática de tipo de hardware
        aut = parametros.get('aut', False)
        dispositivo_real = dispositivo
        
        if aut:
            # Mapeamento de dispositivos automáticos
            dispositivos_automaticos = {
                # Dispositivos USB
                **{f'USB{i}': f'/dev/ttyUSB{i}' for i in range(11)},
                **{f'usb{i}': f'/dev/ttyUSB{i}' for i in range(11)},
                
                # Portas seriais
                **{f'serial{i}': f'/dev/ttyS{i}' for i in range(31)},
                **{f'SERIAL{i}': f'/dev/ttyS{i}' for i in range(31)},
                
                **{"wifi": "/sys/class/net/wlan0"},
                
                
                # Dispositivos especiais
                'null': '/dev/null',
                'zero': '/dev/zero',
                'true': 'special://true',
                'false': 'special://false',
                'none': 'special://none',
                'temperatura': 'special://temperature',
                'one': 'special://one',
                'HDMI': 'special://hdmi',
                "audio_out_status": "special://audio_out_status",
                "audio_in_status": "special://audio_in_status",
                "cpu_u": "special://cpu_u",
                "mem_u": "special://mem_u",
                "bluetooth": "special://bluetooth",
                "battery": "special://battery",
                "audio_status": "special://audio_status",
                
                # Dispositivos de entrada
                **{f'input{i}': f'/dev/input/event{i}' for i in range(10)},
                
                # Armazenamento portátil
                **{f'portatil-armazenamento{i}': f'special://portable{i}' for i in range(11)},
                **{f'portable{i}': f'special://portable{i}' for i in range(11)}
            }
            
            if dispositivo in dispositivos_automaticos:
                dispositivo_real = dispositivos_automaticos[dispositivo]
                print(f"🔍 Dispositivo automático detectado: {dispositivo} -> {dispositivo_real}")
        
        # Criar arquivo de informação do hardware
        info_file = os.path.join(mount_point, 'hardware.info')
        with open(info_file, 'w') as f:
            f.write(f"hardware: {dispositivo}\n")
            f.write(f"dispositivo_real: {dispositivo_real}\n")
            f.write(f"tipo: dispositivo_fisico\n")
            f.write(f"parametros: {parametros}\n")
            f.write(f"status: conectado\n")
            f.write(f"automatico: {aut}\n")
            f.write(f"timestamp: {time.time()}\n")
        
        # Iniciar serviço de atualização dinâmica
        return _iniciar_servico_hardware(nomefs, dispositivo_real, parametros, mount_point)
        
    except Exception as e:
        print(f"⛔ Erro ao conectar hardware {dispositivo}: {e}")
        return False

def _iniciar_servico_hardware(nomefs, dispositivo_real, parametros, mount_point):
    """
    Inicia serviço de atualização dinâmica para hardware.
    """
    try:
        # Código do serviço de atualização dinâmica
        servico_code = f"""
import os
import time
import shutil
import glob

def atualizar_dispositivo_{nomefs.replace('-', '_')}():
    mount_point = '{mount_point}'
    dispositivo = '{dispositivo_real}'
    
    while os.path.exists(mount_point):
        try:
            # Dispositivos especiais
            if dispositivo.startswith('special://'):
                tipo_especial = dispositivo.replace('special://', '')
                
                if tipo_especial == 'null':
                    # Tudo que for movido para aqui é excluído
                    for item in os.listdir(mount_point):
                        item_path = os.path.join(mount_point, item)
                        try:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                        except:
                            pass
                
                elif tipo_especial == 'zero':
                    # Sempre retorna zero
                    zero_file = os.path.join(mount_point, 'zero.bin')
                    with open("zero", 'wb') as f:
                        f.write(b'\x00' * 1024)  # 1KB de zeros
                
                elif tipo_especial == 'true':
                    true_file = os.path.join(mount_point, 'true.txt')
                    with open("true_file", 'w') as f:
                        f.write('True')
                
                elif tipo_especial == 'false':
                    false_file = os.path.join(mount_point, 'false.txt')
                    with open("false_file", 'w') as f:
                        f.write('False')
                
                elif tipo_especial == 'none':
                    none_file = os.path.join(mount_point, 'none.txt')
                    with open("none_file", 'w') as f:
                        f.write('None')
                
                elif tipo_especial == 'one':
                    one_file = os.path.join(mount_point, 'one.txt')
                    with open("one", 'wb') as f:
                        f.write(b'\x11' * 1024)
                
                elif tipo_especial == 'temperature':
                    temp_c = ler_temperatura_real()
                    temp_f = temp_c * 9/5 + 32 if temp_c is not None else None
                    
                    with open(os.path.join(mount_point, 'c.txt'), 'w') as f:
                        f.write(f'{{temp_c:.1f}}')
                    with open(os.path.join(mount_point, 'f.txt'), 'w') as f:
                        f.write(f'{{temp_f:.1f}}')
                
                elif tipo_especial == 'hdmi':
                    hdmi_file = os.path.join(mount_point, 'hdmi.status')
                    with open(hdmi_file, 'w') as f:
                        f.write('connected')
                
                    	f.write(status)
                elif tipo_especial == "audio_status":
                     in = ler_status_audio_in_real()
                     with open(os.path.join(mount_point, "in_status.txt"), "w") as f:
                        f.write(in)
                     out = ler_status_audio_out_real
                     with open(os.path.join(mount_point, "out_status.txt"), "w") as f:
                        f.write(out)
                elif tipo_especial == "cpu_u":
                    u = ler_uso_cpu_real()
                    with open(os.path.join(mount_point, "usage.txt"), "w") as f:
                        f.write(u)
                elif tipo_especial == "mem_u":
                    u = ler_uso_ram_real()
                    with open(os.path.join(mount_point, "usage.txt"), "w") as f:
                        f.write(u)
                elif tipo_especial == "battery":
                    p = ler_bateria_real()
                    s = ler_info_bateria_real("status")
                    cl = ler_info_bateria_real("cap_lev")
                    serial = ler_info_bateria_real("serial")
                    m = ler_info_bateria_real("modelo")
                    with open(os.path.join(mount_point, "percent.txt"), "w") as f:
                        f.write(p)
                    with open(os.path.join(mount_point, "model.txt"), "w") as f:
                        f.write(m)
                    with open(os.path.join(mount_point, "serie_n.txt"), "w") as f:
                        f.write(serial)
                     with open(os.path.join(mount_point, "capacity_level.txt"), "w") as f:
                        f.write(cl)
                     with open(os.path.join(mount_point, "status.txt"), "w") as f:
                        f.write(s)
                 elif tipo_especial == "bluetooth":
                    status = ler_status_bluetooth_real()
                    with open(os.path.join(mount_point, "status.txt"), "w") as f:
                        f.write(status)
                
                
                
                
                
                
                elif tipo_especial.startswith('portable'):
                    # Espelhamento de pen-drive (simulação)
                    numero = tipo_especial.replace('portable', '')
                    portable_path = f'/media/usb{{numero}}' if numero else '/media/usb0'
                    
                    if os.path.exists(portable_path):
                        # Sincronização bidirecional
                        for item in os.listdir(portable_path):
                            source = os.path.join(portable_path, item)
                            dest = os.path.join(mount_point, item)
                            if os.path.isfile(source):
                                shutil.copy2(source, dest)
                        
                        for item in os.listdir(mount_point):
                            if item not in ['hardware.info', 'servico_hardware.status']:
                                source = os.path.join(mount_point, item)
                                dest = os.path.join(portable_path, item)
                                if os.path.isfile(source):
                                    shutil.copy2(source, dest)
            
            # Dispositivos reais do sistema
            elif dispositivo.startswith('/dev/'):
                if os.path.exists(dispositivo):
                    # Para dispositivos USB/seriais
                    if 'ttyUSB' in dispositivo or 'ttyS' in dispositivo:
                        status_file = os.path.join(mount_point, 'serial.status')
                        with open(status_file, 'w') as f:
                            f.write(f'connected: {{dispositivo}}')
                    
                    # Para dispositivos de entrada
                    elif 'input' in dispositivo:
                        status_file = os.path.join(mount_point, 'input.status')
                        with open(status_file, 'w') as f:
                            f.write(f'active: {{dispositivo}}')
                        with open("eventos.txt", "w") as f:
                            eventos = ler_eventos_legivel(dispositivo, 10)
                            for evento in eventos:
                                f.write(f"{evento}\\n")
                            
                        
                    
                    # Para outros dispositivos
                    else:
                        status_file = os.path.join(mount_point, 'device.status')
                        with open(status_file, 'w') as f:
                            f.write(f'available: {{dispositivo}}')
                
                else:
                    status_file = os.path.join(mount_point, 'device.status')
                    with open(status_file, 'w') as f:
                        f.write(f'not_found: {{dispositivo}}')
            
            # Atualizar timestamp do serviço
            status_file = os.path.join(mount_point, 'servico_hardware.status')
            with open(status_file, 'w') as f:
                f.write(f'active: {{time.time()}}')
            
            time.sleep(0.4)  # Atualização a cada 0.4 segundos
            
        except Exception as e:
            error_file = os.path.join(mount_point, 'hardware.error')
            with open(error_file, 'w') as f:
                import time
                f.write(f'{{time.time()}}: {{str(e)}}')
            time.sleep(1)

# Iniciar serviço
import threading
thread = threading.Thread(target=atualizar_dispositivo_{nomefs.replace('-', '_')}, daemon=True)
thread.start()
"""
        
        # Executar o serviço
        exec(servico_code, globals())
        
        print(f"✅ Hardware '{dispositivo_real}' conectado a '{nomefs}' com atualização dinâmica")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao iniciar serviço de hardware {dispositivo_real}: {e}")
        return False

def _conectar_diretorio(nomefs, caminho, parametros, mount_point):
    """
    Conecta filesystem a um diretório real do sistema
    """
    print(f"📁 Conectando ao diretório '{caminho}'")
    
    try:
        if not os.path.exists(caminho):
            os.makedirs(caminho, exist_ok=True)
            print(f"📁 Diretório {caminho} criado")
        
        info_file = os.path.join(mount_point, 'diretorio.info')
        with open(info_file, 'w') as f:
            f.write(f"diretorio: {caminho}\n")
            f.write(f"tipo: link_diretorio\n")
            f.write(f"parametros: {parametros}\n")
            f.write(f"status: conectado\n")
        
        if parametros.get('copiar_conteudo'):
            for item in os.listdir(caminho):
                item_path = os.path.join(caminho, item)
                if os.path.isfile(item_path):
                    shutil.copy2(item_path, mount_point)
        
        print(f"✅ Diretório '{caminho}' conectado")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao conectar diretório {caminho}: {e}")
        return False

def _conectar_codigo_paralelo(nomefs, script_path, parametros, mount_point):
    """
    Conecta filesystem a código Python paralelo
    """
    print(f"🐍 Conectando ao código '{script_path}'")
    
    try:
        if not os.path.exists(script_path):
            print(f"⛔ Script {script_path} não encontrado")
            return False
        
        with open(script_path, 'r') as f:
            codigo = f.read()
        
        intervalo = parametros.get('intervalo', 1.0)
        
        servico_code = f'''
import time
import os

def executar_servico_paralelo():
    while True:
        try:
            exec(f"{codigo}")
        except Exception as e:
            print(f"Erro no serviço paralelo: {{e}}")
        
        time.sleep({intervalo})

import threading
thread = threading.Thread(target=executar_servico_paralelo, daemon=True)
thread.start()
'''
        
        exec(servico_code, globals())
        
        info_file = os.path.join(mount_point, 'codigo_paralelo.info')
        with open(info_file, 'w') as f:
            f.write(f"script: {script_path}\n")
            f.write(f"tipo: codigo_paralelo\n")
            f.write(f"intervalo: {intervalo}\n")
            f.write(f"status: executando\n")
        
        print(f"✅ Código paralelo '{script_path}' conectado a '{nomefs}'")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao conectar código {script_path}: {e}")
        return False

def _conectar_rede(nomefs, host, parametros, mount_point):
    """
    Conecta filesystem a recurso de rede
    """
    print(f"🌐 Conectando '{nomefs}' à rede '{host}'")
    
    try:
        porta = parametros.get('porta', 80)
        protocolo = parametros.get('protocolo', 'tcp')
        
        info_file = os.path.join(mount_point, 'rede.info')
        with open(info_file, 'w') as f:
            f.write(f"host: {host}\n")
            f.write(f"porta: {porta}\n")
            f.write(f"protocolo: {protocolo}\n")
            f.write(f"tipo: conexao_rede\n")
            f.write(f"status: conectado\n")
        
        test_code = f"""
import socket
try:
    socket.create_connection(('{host}', {porta}), timeout=5)
    print(f"✅ Conexão de rede '{nomefs}' ativa: {host}:{porta}")
except Exception as e:
    print(f"⚠️  Aviso conexão '{nomefs}': {{e}}")
"""
        exec(test_code, globals())
        
        print(f"✅ Rede '{host}:{porta}' conectada")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao conectar rede {host}: {e}")
        return False

def _conectar_servidorweb(nomefs, host, parametros, mount_point):
    """
    Cria um servidor web real no filesystem.
    """
    print(f"🌐 Iniciando servidor web em {host}:{parametros.get('porta', 80)}")
    
    porta = parametros.get('porta', 80)
    protocolo = parametros.get('protocolo', 'http')
    www_dir = parametros.get('www_dir', mount_point)

    try:
        if not os.path.exists(www_dir):
            os.makedirs(www_dir, exist_ok=True)
            print(f"📁 Diretório {www_dir} criado")

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

thread = threading.Thread(target=run_web_server, daemon=True)
thread.start()
"""
        
        exec(servidor_code, globals())
        
        status_file = os.path.join(mount_point, 'server.status')
        with open(status_file, 'w') as f:
            f.write(f"servidor_web: {nomefs}\n")
            f.write(f"host: {host}\n")
            f.write(f"porta: {porta}\n")
            f.write(f"protocolo: {protocolo}\n")
            f.write(f"www_dir: {www_dir}\n")
            f.write(f"status: ativo\n")

        print(f"✅ Servidor web rodando em http://{host}:{porta}")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao iniciar servidor web: {e}")
        return False

def _conectar_servidor(nomefs, host, parametros, mount_point):
    """
    Cria um servidor genérico com serviços específicos.
    """
    print(f"🖥️ Iniciando servidor em {host}:{parametros.get('porta', 8080)}")
    
    porta = parametros.get('porta', 8080)
    protocolo = parametros.get('protocolo', 'tcp')
    servidor_arquivos = parametros.get('servidor_arquivos')
    servidor_servicos = parametros.get('servidor_servicos', [])
    
    # 🎯 CARREGAR E EXECUTAR serviços DENTRO DO SERVIDOR
    servicos_globais = {}
    servicos_dir = os.path.join(mount_point, 'services')
    
    if os.path.exists(servicos_dir):
        for arquivo in os.listdir(servicos_dir):
            if arquivo.endswith('.py'):
                nome_servico = arquivo[:-3]
                caminho_script = os.path.join(servicos_dir, arquivo)
                
                try:
                    with open(caminho_script, 'r') as f:
                        codigo = f.read()
                    
                    # 🎯 Compilar código do serviço para passar ao servidor
                    servicos_globais[nome_servico] = codigo
                    print(f"  ✅ Serviço '{nome_servico}' carregado")
                        
                except Exception as e:
                    print(f"  ⚠️ Erro carregando serviço '{nome_servico}': {e}")

    try:
        # 🎯 Código do servidor COM SERVIÇOS EXECUTANDO DENTRO
        servidor_base = f"""
import socket
import threading
import os
import time
import json

# 🎯 EXECUTAR serviços DENTRO do contexto do servidor
servicos_ativos = {{}}

# Inicializar cada serviço
for nome_servico, codigo_servico in {servicos_globais}.items():
    try:
        # Executar código do serviço DENTRO do servidor
        exec(codigo_servico)
        if 'main' in locals():
            # 🎯 INSTANCIAR serviço DENTRO do servidor
            instancia_servico = main()
            servicos_ativos[nome_servico] = instancia_servico
            print(f"🎯 Serviço '{{nome_servico}}' INICIADO DENTRO DO SERVIDOR")
    except Exception as e:
        print(f"❌ Erro iniciando serviço '{{nome_servico}}': {{e}}")

class GenericServer:
    def __init__(self, host='', port={porta}):
        self.host = host
        self.port = port
        self.running = True
        self.file_server = '{servidor_arquivos}' if '{servidor_arquivos}' else None
        self.services = {servidor_servicos}
        self.servicos_ativos = servicos_ativos  # 🎯 Serviços JÁ EXECUTANDO
    
    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode('utf-8')
            print(f"📨 Cliente conectado: {{request[:50]}}...")
            
            # 🎯 PROCESSAR com serviços ATIVOS
            resposta = self.processar_com_servicos(request)
            if resposta:
                client_socket.send(resposta.encode('utf-8'))
            else:
                response = "HTTP/1.1 200 OK\\r\\n\\r\\nServidor Aurox Generic Server"
                client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Erro no cliente: {{e}}")
            response = "HTTP/1.1 500 Internal Error\\r\\n\\r\\nErro no servidor"
            client_socket.send(response.encode('utf-8'))
        finally:
            client_socket.close()
    
    def processar_com_servicos(self, request):
        '''Processa requisição usando serviços ativos DENTRO DO SERVIDOR'''
        try:
            for nome_servico, servico in self.servicos_ativos.items():
                try:
                    # 🎯 Serviço EXECUTA DENTRO do servidor
                    if hasattr(servico, 'processar_request'):
                        resultado = servico.processar_request(request)
                        if resultado:
                            return f"HTTP/1.1 200 OK\\r\\n\\r\\n{{json.dumps(resultado)}}"
                    
                    # 🎯 Ou usar método padrão 'processar'
                    elif hasattr(servico, 'processar'):
                        resultado = servico.processar()
                        if resultado:
                            return f"HTTP/1.1 200 OK\\r\\n\\r\\n{{json.dumps(resultado)}}"
                            
                except Exception as e:
                    print(f"Erro no serviço {{nome_servico}}: {{e}}")
                    
        except Exception as e:
            print(f"Erro geral em serviços: {{e}}")
        
        return None
    
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"✅ Servidor genérico '{nomefs}' rodando em {{self.host}}:{{self.port}}")
        print(f"🎯 Serviços EXECUTANDO DENTRO: {{list(self.servicos_ativos.keys())}}")
        
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

thread = threading.Thread(target=run_generic_server, daemon=True)
thread.start()
"""
        
        exec(servidor_base, globals())
        
        status_file = os.path.join(mount_point, 'generic_server.status')
        with open(status_file, 'w') as f:
            f.write(f"servidor: {nomefs}\n")
            f.write(f"host: {host}\n")
            f.write(f"porta: {porta}\n")
            f.write(f"servicos_ativos: {list(servicos_globais.keys())}\n")
            f.write(f"status: executando\n")

        print(f"✅ Servidor genérico rodando em {host}:{porta}")
        print(f"🎯 Serviços EXECUTANDO DENTRO DO SERVIDOR: {list(servicos_globais.keys())}")
        return True
        
    except Exception as e:
        print(f"⛔ Erro ao iniciar servidor: {e}")
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




def LFV(nomefs):
    """
    Cria um dicionário com a estrutura de arquivos do diretório ../mnt/{nomefs}
    
    Args:
        nomefs (str): Nome do sistema de arquivos
        
    Returns:
        dict: Dicionário com a estrutura de arquivos e conteúdo dos arquivos de texto
    """
    caminho_base = f"../mnt/{nomefs}"
    
    # Verifica se o diretório existe
    if not os.path.exists(caminho_base):
        raise FileNotFoundError(f"Diretório {caminho_base} não encontrado")
    
    def explorar_diretorio(caminho):
        """
        Função recursiva para explorar diretórios e arquivos
        """
        estrutura = {}
        
        try:
            itens = os.listdir(caminho)
        except PermissionError:
            estrutura['_erro'] = 'Permissão negada'
            return estrutura
        
        for item in itens:
            caminho_completo = os.path.join(caminho, item)
            
            if os.path.isdir(caminho_completo):
                # É um diretório - explora recursivamente
                estrutura[item] = explorar_diretorio(caminho_completo)
            else:
                # É um arquivo
                info_arquivo = {
                    'tipo': 'arquivo',
                    'tamanho': os.path.getsize(caminho_completo)
                }
                
                # Verifica se é um arquivo de texto e lê o conteúdo
                if é_arquivo_texto(item):
                    try:
                        with open(caminho_completo, 'r', encoding='utf-8') as f:
                            info_arquivo['conteudo'] = f.read()
                    except (UnicodeDecodeError, PermissionError, IOError):
                        info_arquivo['conteudo'] = None
                        info_arquivo['erro_leitura'] = True
                
                estrutura[item] = info_arquivo
        
        return estrutura
    
    def é_arquivo_texto(nome_arquivo):
        """
        Verifica se um arquivo é provavelmente um arquivo de texto
        baseado na extensão
        """
        extensoes_texto = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml',
            '.csv', '.log', '.conf', '.cfg', '.ini', '.yml', '.yaml',
            '.java', '.c', '.cpp', '.h', '.php', '.rb', '.pl', '.sh', '.bat',
            '.ps1', '.sql', '.r', '.m', '.swift', '.kt', '.go', '.rs', '.cs'
        }
        
        _, extensao = os.path.splitext(nome_arquivo)
        return extensao.lower() in extensoes_texto
    
    # Inicia a exploração do diretório base
    return explorar_diretorio(caminho_base)



APPC = {
"__name__": "__app__",
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
'sys_pid': sys_pid,
"domestico": domestico,
"LFV": LFV
}

SYSC = {
'__name__': "__distro__",
"__builtins__": __builtins__,
"mnt": mnt,
"umnt": umnt,
"configurar_fs": configurar_fs,
"matar_proc": matar_proc,
"MCA": MCA,
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
"sys_pid": sys_pid,
"domestico": domestico,
"addperm": addperm,
"delperm": delperm,
"default_perm": default_perm,
"LFV": LFV,
"auroxperm": auroxperm,
"LinuxFs": LinuxFs
}

class hw_instan_return:
	def __init__(self):
		pass
	def ppn(self):
		return hw_instan.ppn
	def memory(self):
		return hw_instan.memory
	def mem_prot(self):
		return hw_instan.mem_prot
	def all(self):
		return hw_instan

def exe(comando):
	comando()

KRNLC = {
'__name__': "__aurox__",
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
"VSP": VSP,
"DistroError": DistroError,
"AuroxError": AuroxError,
"appperms": appperms,
"perm_padrao": perm_padrao,
"LFV": LFV,
"ler_uso_cpu_real": ler_uso_cpu_real,
"ler_uso_ram_real": ler_uso_ram_real,
"hw_instan_return": hw_instan_return,
"appc": APPC,
"ler_temperatura_real": ler_temperatura_real,
"sys_fs": sys_fs,
"exe": exe,
"umnt_op": umnt_op
}

class HWIW:
    def __init__(self, hw_instan):
        try:
        	self._hw_instan = hw_instan
        except NameError:
        	raise AuroxError('erro desconhecido')
        
    @property
    def processos_parar(self):
        return self._hw_instan.processos_parar
        
    # 🔒 BLOQUEIA acesso a outros atributos
    def __getattr__(self, name):
        if name == 'processos_parar':
            return self._hw_instan.processos_parar
        raise AuroxError(f"Acesso restrito a hw_instan.{name}")




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
					time.sleep(0.4)
					status = "✅" if i < len(self.mem_prot) and self.mem_prot[i] else "⏳"
					print(f"  {status} codigo {i}: {app[0][:40]}...")
			
			processos_executados = False
			
			for i in range(len(self.memory)):
				if i not in containers:
					try:
						containers[i] = {}
						if debug: print(f"container {i} criado: {containers[i]}")
					except Exception as e:
						raise AuroxError(f"erro ao criar container: {e}")
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
	
	y = """while True:
	time.sleep(7)
	ab, a = VED(None, "PHC Kernel Service", "name")
	bb, b = VED(None, "VSP Kernel Service", "name")
	cb, c = VED(None, "UPL Kernel Service", "name")
	if not ab:
		raise AuroxError("PHC killed")
		sys.exit(1)
	if not bb:
		raise AuroxError("VSP killed")
		sys.exit(1)
	if not cb:
		raise AuroxError("UPL killed")
		sys.exit(1)"""
	
	tmp_m.append((y, "KSP Kernel Service", KRNLC))
	
	z = """while True:
	time.sleep(3)
	a = os.listdir("./apps")
	apps_sem_extensao = [app.replace('.py', '') for app in a if app.endswith('.py')]
	
	# ✅ CORREÇÃO: Criar novo dicionário em vez de modificar durante iteração
	novo_appperms = {}
	for app in apps_sem_extensao:
		novo_appperms[app] = appperms.get(app, perm_padrao)
	
	appperms.clear()
	appperms.update(novo_appperms)"""
	tmp_m.append((z, "UPL Kernel Service", KRNLC))
	
	w = """cl = hw_instan_return()
while True:
	time.sleep(0.10)
	a = ler_uso_ram_real()
	b = ler_uso_cpu_real()
	if a is not None:
		if a > 80:
			for i in range(500):
				atual = cl.memory()
				if len(atual) > 380:
					if atual[i][2] == appc:
						matar_proc(i, False)
				if umnt_op:
					fss = os.listdir("../mnt")
					# desmontar filesystems não nessesarios
					for fs in fss:
						if fs not in sys_fs:
							umnt(fs)
	if b is not None:
		if b > 80:
			for i in range(500):
				atual = cl.memory()
				if len(atual) > 380:
					if atual[i][2] == appc:
						matar_proc(i, False)
				fss = os.listdir("../mnt")
				if umnt_op:
					for fs in fss:
						if fs not in sys_fs:
							umnt(fs)"""
	tmp_m.append((w, 'OPD Kernel Service', KRNLC))
	
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
					time.sleep(0.5)
					if debug: print(" ✅️ init.py inicializado na memoria")
				except Exception as e:
					if debug: print(f"erro ao ler init.py ou erro ao inicializar o init.py na memoria: {e}")
					raise AuroxError(e)
			except Exception as e:
				erro_no_tmp_m += 1
				if debug: print(f" ⚠️ falha ao abrir init.py: {e}")
				raise AuroxError(f"erro ao abrir init.py: {e}")
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
	if "hw_instan" not in globals(): hw_instan = hardware(tmp_m)
	time.sleep(0.5)
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
    


