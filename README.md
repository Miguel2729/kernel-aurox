![logo](logo10_17_10307.png)

O **Kernel Aurox** é um script python que implementa funcionalidades de um kernel sem simulação(para fins produtivos) projetado para criar **distribuições personalizadas** do sistema Aurox.  
Ele é **educacional**(educacional se o professor tiver cuidado porque o aurox é produtivo) e **produtivo** e permite montar e fazer ambientes completos com suporte a processos, arquivos, sistemas de arquivos, pacotes e até aplicativos, ele também não é complexo mais também não é limitado, ele é poderoso e simples

---

## 📁 Estrutura de Arquivos Esperada

Cada distribuição Aurox deve seguir esta estrutura:

```
.
├── system
│   ├── code
│   │   ├── init.py # (opcional) inicia a distro
│   │   └── *.py # outros serviços e deamons da distro
│   ├── modules # modulos da distro
│   ├── tmp # arquivos temporarios
│   ├── apps #(opcional) Aplicativos 
│   ├── lib32 # bibliotecas 32 bits, módulos .c, .so, .dll
│   ├── lib64 # bibliotecas 64 bits módulos .c, .so, .dll
│   ├── lib  # (opcional) se você quiser deixar mais organizado mova lib32 e lib64 para aqui
│   ├── etc
│   │   ├── systemd # systemd
│   │   │   ├── systemd.py - codigo systemd(processo executado no globals())
│   │   │   ├── *.mnt # .ini de montagem automática 
│   │   │   └── *.umnt # .ini de desmontagem automática
│   │   ├── shells.txt # shells disponíveis
│   │   └── shell.txt # shell usado, deve estar listado em shells.txt, default para o shell da distro
│   └── framework # pacotes do framework, .pkg e .apkg
├── mnt/ # filesystems montados
├── pkg/ # pacotes instalados
├── kernel.py # kernel
└── boot.ini # configuração de boot

```

---




## ⚙️ Classe `distro`

A classe `distro` é usada pelas distribuições Aurox para definir nome, versão, serviços, arquivos e IPC (comunicação entre processos).

### Exemplo:

```python
testsOS = distro(
	nome="MinhaDistro", ver="1.0",
	fs=["rootfs"], nomefs=["sistema"],
	cfgfs=[("diretorio", "/tmp", {"sync_mode": "mirror", "intervalo": 0.10})],
	services=["vfs.py", "audio.py", "tools.py"],
	serv_reset_m=False,
	ipc=True
	ufs=True # significa "umount filesystems on shutdown",
	pkgs=[["gabriel123", "editor"], ["enzo46321", "internet"]]
)
```

---

## 💡 Dicas para Desenvolvedores

### O que colocar em `system/code/`

- `init.py`: script de inicialização principal (o único a ser executado se existir)  
- Serviços e daemons em background    
- Drivers simulados(ou não) com `configurar_fs()`

### 🗂 desenvolvimento pacotes aurox
---
deve ser um repositório do github
estrutura do repositório:
```tree
[pacote]-aurox-pkg
└── [pacote].py
```
por exemplo se a distro tentar instalar um pacote chamado "editor", o aurox irá converter para "editor-aurox-pkg"
#### como dev ser [pacote].py?:
deve ser um módulo python, cada comando do pacote deve ser uma função(def), e a função main é obrigatória para comportamento padrão, todas as funções deve ter apenas um parâmetro, que vai ser uma tupla ou lista com todos os parâmetros da função

- não deve ter mais arquivos além do [pacote].py, se possível
---

### Exemplo de `init.py`

```python
print("🚀 Inicializando Minha Distribuição Aurox...")

# Montar filesystems essenciais
mnt("rootfs", "sistema")

# Configurar conexões
configurar_fs("sistema", "diretorio", "/tmp", {"sync_mode": "mirror", intervalo: 0.10})

print("✅ Sistema inicializado com sucesso!")
```

---

## 🔧 Funções do Kernel

### 🧠 Gerenciamento de Processos

```python
matar_proc(pid, log)
# Mata um processo pelo PID

listar_proc(printp)
# Lista todos os processos ativos
# Retorna: [[pid, nome], ...]

criar_processo_filho(pai, nome, codigo)
# cria um processo filho, o Parâmetro pai deve ser um pid numérico, de preferência de tipo int para o encerramento do pai encerrar o filho corretamente

CPFS(pai, nome, codigo)
# a mesma coisa criar_processo_filho, só que inicia no contexto do SYSC, apenas a distro(apps não) tem acesso ao CPFS
```

```python
pwroff_krnl()
# Desliga o sistema e encerra todos os processos

reboot()
# reinicia o sistema
```
### apps
```python
initapp(app, reset_m, log)
# log deve ser True ou False
# reset_m também
# se reset_m for True o initapp vai resetar a memória para iniciar o aplicativo
# diretorio recomendado de apps:
# system/apps
```

---

### 💾 Gerenciamento de Filesystems

```python
mnt(fs, nomefs)
# Monta um filesystem

umnt(nomefs)
# Desmonta um filesystem
configurar_fs(nomefs, tipo, destino, parametros)
# Configura um filesystem montado
# Tipos: 'hardware', 'diretorio', 'codigo_paralelo', 'rede'
# Parâmetros por tipo:
#   'hardware': aut
#   'diretorio': sync_mode, criar_diretorio, intervalo
#   'codigo_paralelo': intervalo
#   'rede': protocolo, porta
#   'servidorweb': www_dir, protocolo, porta
#   'servidor': protocolo, porta, servidor_arquivos, servidor_servicos
# para obter mais informações pode olhar o código de kernel.py, não tem problema, é licença MIT

LFV(nomefs)
# lista recursiva e com conteúdo de arquivos de texto dos arquivos de um filesystem

```
---
### 🔐 permissões
```python
# apenas no namespace SYSC
# permissões possíveis:
# net
# filesystems
# matar
# matarsys
# ambiente
# sistema

addperm(app, perm)
# adiciona permissão
delperm(app, perm)
# Remove permissão
default_perm(app)
# redefinir permissões para padrão

MCA(appc)
# modifica o namespace "APPC" para o Parâmetro "appc"
```
---
---

### 🔗 Comunicação entre Processos (IPC)

```python
IPC(destino, msg, assina_por_pid, assina_por_nome)
# Envia mensagem IPC para outro processo, assina_por_pid é o pid do remetente, assina_por_nome é o nome do remetente

ler_IPC(pid)
# Lê mensagens recebidas pelo processo

limpar_IPC(pid)
# Limpa o buffer IPC do processo
```
---
# 🗂 Gerenciamento de pacotes
```python
installpkg(dev, pkg)
# instala um pacote, github, requer git instalado

delpkg(pkg)
# deleta um pacote

usepkg(pkg, comando="main", parametros=())
# usa um pacote

checkpkg(pkg)
# verifica se um pacote existe
```

VED(pid, nome, x)
# Localiza processos ativos pelo PID ou nome.
# Retorna (True, valor_encontrado) ou (False, None).

# Parâmetros:
# pid (int): identificador do processo
# nome (str): nome do processo
# x (str): modo de busca
#           - "pid" → retorna o nome do processo a partir do PID
#           - "name" → retorna o PID a partir do nome

exemplo:
```
# Obter nome a partir do PID
ok, nome = VED(1, None, "pid")

# Obter PID a partir do nome
ok, pid = VED(None, "init", "name")
```
---
---
# namespaces do kernel
- o kernel executa namespaces separados para apps e a distro e o kernel
namespaces:

```
# b_filt é uma versão filtrada do builtins
# modulotmp e modulotmp2 são versões seguras dos módulos os e shutil
# open_customizado é versão segura do open

APPC = {
"__name__": "__app__",
"VED": VED,
"matar_proc": matar_proc,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"criar_processo_filho": criar_processo_filho,
"__builtins__":  b_filt,
"open": open_customizado,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg,
"os": modulotmp,
"time": time,
"shutil": modulotmp2,
"import2": __import__,
"random": random,
'sys_pid': sys_pid,
"domestico": domestico,
"LFV": LFV,
"keyboard": keyboard if infos["kb_forced_reboot_key"] else None,
"exec_aex": exec_aex_app,
"__colors__": Cores,
"gdioad": gdioad,
"sharedata": sharedata
}



SYSC = {
'__name__': "__distro__",
"__builtins__": b_filt,
"open": open_customizado,
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
"os": modulotmp,
"sys": sys,
"time": time,
"shutil": modulotmp2,
"random": random,
"import2": __import__,
"sys_pid": sys_pid,
"domestico": domestico,
"addperm": addperm,
"delperm": delperm,
"default_perm": default_perm,
"LFV": LFV,
"auroxperm": auroxperm,
"LinuxFs": LinuxFs,
"VED": VED,
"keyboard": keyboard if infos["kb_forced_reboot_key"] else None,
"exec_aex": exec_aex,
"__colors__": Cores,
"gdioad": gdioad,
"sharedata": sharedata
}

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
"umnt_op": umnt_op,
"__colors__": Cores
}

SHC = {
'__name__': "__shell__",
"__builtins__": b_filt,
"open": open_customizado,
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
"shutil": modulotmp2,
"random": random,
"import2": __import__,
"sys_pid": sys_pid,
"domestico": domestico,
"addperm": addperm,
"delperm": delperm,
"default_perm": default_perm,
"LFV": LFV,
"auroxperm": auroxperm,
"LinuxFs": LinuxFs,
"VED": VED,
"keyboard": keyboard if infos["kb_forced_reboot_key"] else None,
"exec_aex": exec_aex,
"__colors__": Cores,
"sharedata": sharedata
}
```


# 📃 como acessar relatório da classe distro?
Para acessar o relatório da classe distro quando você está criando sua distribuição Aurox, você precisa criar uma instância da classe distro e armazenar essa instância em uma variável. Após a inicialização da distro, o relatório estará disponível no atributo .relat dessa instância.

Por exemplo, no seu código de inicialização da distro (normalmente no arquivo init.py dentro de system/code), você faria assim:

minha_distro = distro(nome="MinhaDistro", ver="1.0", fs=lista_fs, nomesfs=lista_nomes, cfgfs=lista_configs, services=lista_servicos, serv_reset_m=False, ipc=True, ufs=True, pkgs=lista_pacotes, umnt_op_cfg=True)

E depois, para acessar o relatório completo:

relatorio = minha_distro.relat

O relatório é um dicionário que contém informações detalhadas sobre o processo de inicialização, incluindo o status de filesystems, serviços e pacotes. Ele tem a seguinte estrutura:

· relat["pkgs"]: relatório de instalação de pacotes
· relat["filesys"]: relatório de montagem e configuração de filesystems
· relat["services"]: relatório de inicialização de serviços

Cada seção do relatório inclui status (ok, errors, partially_ok), contagem de erros e sucessos, timestamp e mensagens de erro detalhadas quando aplicável.

relatório no teste do desenvolvedor(Miguel2729):
```output
status_idle: True
/storage/emulated/0/teste
modo debug?(S/n): n
tee: /etc/shells: Read-only file system
./shell
🎯 Executando 0 serviços do sistema
/storage/emulated/0/teste/system>relat

{'pkgs': {'status': 'ok', 'errors': 0, 'successfully': 0, 'time': 1762614721.3094807, 'err_msg': {}}, 'filesys': {'status': 'ok', 'errors': 0, 'successfully': 0, 'time': 1762614721.3193884, 'err_msg': {}}, 'services': {'status': 'ok', 'errors': 0, 'successfully': 0, 'time': 1762614721.3194084, 'err_msg': {}}}

/storage/emulated/0/teste/system>
```
---
# ⚠️ Avisos Importantes

- ⚙️ pode ser usado em contextos educacionais, Simulações e produtivos
- 💾 cuidado com configurar_fs, ele não é simulado
- 🧪 Teste extensivamente os serviços antes de distribuir.  
- 🔁 while True em processos são modificados pelo kernel para parar em caso de encerrar o processo
- 🧹 Use `matar_proc()` e `pwroff_krnl()` para encerrar processos corretamente.  
- 🔐 Verifique permissões do arquivo `shell`.
- ✅️ os processos são executados dentro do kernel em contexto global, não como módulos separados, pode se comunicar(usar funções do kernel) com o kernel sem importar
- 📦 todos os processos tem um container criado pelo kernel, não é preciso se preocupar com o nome das variávei
- ▶️ na lista do parâmetro services da classe distro, coloque os serviços na ordem que deseja que eles sejam inicializados
- 🚫 se o desenvolvedor perceber simulação ele transforma em funcional
- 🚨 pressione ctrl + f + r para forçar reinicio
- 📝 os formato de arquivos inventados pelo aurox são, .aex, .mnt, .umnt, .pkg, .apkg
- >_ shell.py é shell e não terminal, ele executa comandos dele que são enviados pelo ipc
---

# COMO CRIAR ARQUIVOS DE CONFIGURAÇÃO DO AUROX

BOOT.INI

O arquivo boot.ini é essencial para inicializar a distro Aurox. Ele deve estar na raiz do sistema.

Estrutura básica:

[boot]
not_init= init.py
init= default
sh_arch= 64
force_debug= false
libp= 64


[compatibility]
s_hostsys= posix, nt
gc= true
perms_default= {"net": true, "matar": true, "matarsys": false, "filesystems": false, "ambiente": false, "sistema": false, "acesso_arquivos": false}
compile_binarys= true
disable_ioput= false


Explicação das seções:

[boot]

· not_init: serviços que a classe distro irá pular
· init: tipo de inicialização (default para padrão)
· sh_arch: arquitetura do shell (8, 16, 32, 64)
· force_debug: forçar modo debug (true/false)
· libp: quais bibliotecas carregar primeiro(32 ou 64)

[compatibility]

· s_hostsys: sistemas operacionais suportados (posix=Linux/Mac, nt=Windows)
· gc: ativar garbage collector (true/false)
· perms_default: permissões padrão para apps
· compile_binarys: compilar binários automaticamente (true/false)
· disable_ioput: desativar input/output (true/false)

ARQUIVOS .MNT (AUTOMOUNT)

Arquivos .mnt são usados pelo systemd para montar filesystems automaticamente. Devem ficar em system/etc/systemd/

Exemplo: network.mnt

[conf]
cond= True
fsname= network
fs= net
mount_script= configurar_fs('network', 'diretorio', '/sys/class/net', {'sync_mode': 'mirror', 'intervalo': 1})
wait= 10

## Estrutura:

· cond: condição para montar (ex: True para sempre, ou uma expressão Python)
· fsname: nome do filesystem
· fs: filesystem a ser montado(nome técnico) · · mount_script: script para configurar após montagem
· wait: intervalo entre verificações (segundos)

ARQUIVOS .UMNT (AUTOUNMOUNT)

Arquivos .umnt são usados para desmontar filesystems automaticamente. Devem ficar em system/etc/systemd/

Exemplo: temp_fs.umnt

[conf]
cond= ler_uso_ram_real() > 80
fsname= temp_fs
wait= 5

## Estrutura:

· cond: condição para desmontar (ex: quando uso de RAM > 80%)
· fsname: nome do filesystem a desmontar
· wait: intervalo entre verificações (segundos)



## NOTAS IMPORTANTES:

· Todos os arquivos devem usar codificação UTF-8
· As condições (cond) são expressões Python válidas
· Os scripts de montagem podem usar qualquer função do kernel
· Mudanças nos arquivos são aplicadas automaticamente

AQUI ESTÁ O TEXTO PARA A DOCUMENTAÇÃO DO AUROX:

COMO CRIAR PACOTES E APLICATIVOS PARA O AUROX

O Aurox suporta três formatos principais de pacotes: .pkg, .apkg e .aex. Cada um tem propósitos específicos e estrutura própria.

FORMATO .PKG (PACOTES SIMPLES)

Um arquivo .pkg é um pacote simples contendo um único módulo Python.

Estrutura:

· arquivo.pkg (renomeie para .py para desenvolvimento)

Requisitos:

· Deve conter uma variável ambs definindo onde será disponibilizado
· O código principal do pacote

Exemplo de código:

ambs = ["sys", "app", "shell"]  # Onde o pacote estará disponível

def minha_funcao():
return "Olá do pacote!"

class MinhaClasse:
def init(self):
self.nome = "Meu Pacote"

O pacote será importado como módulo Python normal

Como usar:

1. Desenvolva o código em um arquivo .py
2. Adicione a variável ambs especificando os namespaces
3. Renomeie para .pkg
4. Coloque em system/framework/

FORMATO .APKG (PACOTES AVANÇADOS)

Um arquivo .apkg é um pacote zipado com estrutura complexa.

Estrutura do diretório:
nome_do_pacote/
├──conf.py
├──self
├──lib/
│└── bibliotecas.c
├──funcs/
│├── static/
││   └── funcoes_estaticas.py
│└── regular/
│└── funcoes_regulares.py
└──módulos_adicionais.py

Arquivos obrigatórios:

1. conf.py - Configuração do pacote:
   ambs= ["sys", "app"]  # Namespaces
   arch= "64"  # Arquitetura
   type_add_class= "<instance>"  # ou "<class>"
2. self - Definição de atributos:
   nome="MeuPacote"
   versao="1.0"
   descricao="Um pacote avançado"
3. Arquivos em funcs/static/ - Funções estáticas:

funcoes_estaticas.py

name = "minha_funcao_estatica"

def main():
return "Função estática executada"

1. Arquivos em funcs/regular/ - Funções regulares:

funcoes_regulares.py

def main(param1, param2):
return f"Parâmetros: {param1}, {param2}"

1. lib/ - Bibliotecas C:

· Arquivos .c serão compilados automaticamente

Como criar:

1. Crie a estrutura de diretórios
2. Desenvolva todos os componentes
3. Compacte para .zip
4. Renomeie para .apkg
5. Coloque em system/framework/

FORMATO .AEX (APLICATIVOS EXECUTÁVEIS)

Um arquivo .aex é um aplicativo executável compactado.

Estrutura do arquivo .aex (renomeie para .zip para editar):

· conf.ini
· exe.py ou exe.code
· exe.type

Arquivos obrigatórios:

1. conf.ini - Configuração:
   [info]
   name= NomeDoApp

[info]
name = nome_do_processo

[compatibility]
suported_distros= all_ou_nome_de_distros_aurox
pkgs= pacote1, pacote2, pacote3

[init]
setup_exe= base64_do_codigo_setup
interpreter= python3_ou_python2_ou_outro_interpretador no sistema

1. exe.type - Tipo de execução:

· "<main>" - Aplicativo principal
· "<plugin>" - Plugin do sistema
· "<library>" - Biblioteca
· "<custom_driver>" - Driver personalizado
· "<interpr>" - interpretador customizado

1. exe.py - Código principal (Python):

Código do aplicativo

def main():
print("Meu aplicativo Aurox!")

if name == "main":
main()

1. exe.code - Código em outras linguagens (opcional)

Como criar um .aex a partir de um app existente:


sucesso, mensagem = exec_aex("app.aex", "<app>")

Namespaces suportados:

· "<app>" - Namespace de aplicativo
· "<sys>" - Namespace do sistema
· Namespace personalizado



CONSIDERAÇÕES IMPORTANTES:


1. Segurança: Código é executado em namespaces restritos
2. Compatibilidade: Verifique as distros suportadas no conf.ini
3. Dependências: Liste todos os pacotes necessários no conf.ini

EXEMPLO COMPLETO DE CRIAÇÃO DE .AEX:



## 🚀 Começando

1. Clone a estrutura base do Aurox  
2. Adicione seus serviços em `system/code/`  
3. Configure filesystems com `mnt()` e `configurar_fs()`  
4. Teste localmente  
5. Distribua sua versão do Aurox  

---

## 🧾 Exemplo de Desligamento

```
shutdown:
desligando...
encerrando processos...
⚠️ init encerrado
⚠️ vfs service encerrado
⚠️ audio service encerrado
⚠️ tools service encerrado
✅ ppn limpado
✅ limpado
Desmontando filesystems...
✅️ filesystems Desmontados
finalizando...
```

---

📘 **Versão:** Kernel Aurox  
📅 **Última atualização:** Outubro de 2025  
👨‍💻 **Autor:** Miguel  
🧩 **Licença:** MIT
