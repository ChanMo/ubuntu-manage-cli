"""
Linux manager cli

chan.mo@outlook.com
22/05/07 16:25
"""
import yaml
import subprocess
from fabric import Connection
from invoke import Responder
import click

with open('./config.yml', 'r') as f:
    text = f.read()

config = yaml.load(text, Loader=yaml.FullLoader).get('default')

sudopass = Responder(
    pattern=r'\[sudo\] password for {}:'.format(config.get('user')),
    response='{}\n'.format(config.get('password'))
)


@click.group()
def cli():
    pass

@click.command()
@click.argument('ip')
@click.argument('user')
@click.argument('password')
@click.argument('ubuntu')
def initvps(ip, user, password, ubuntu="22.04"):
    """
    初始化服务器
    v0.1.1
    17:07:58 28/05/20

    * 提前设置好安全组2112
    """
    c = Connection(host=ip, user=user, connect_kwargs={'password':password})
    init_sudopass = Responder(
        pattern=r'\[sudo\] password for {}:'.format(user),
        response='{}\n'.format(password)
    )

    c.run('sudo apt-get update -y', watchers=[init_sudopass])
    c.run('sudo groupadd chen', watchers=[init_sudopass])
    c.run('sudo useradd -m -g chen -s /bin/bash chen', watchers=[init_sudopass])
    c.run('sudo passwd chen', watchers=[init_sudopass])
    c.run('echo "chen ALL=(ALL:ALL) ALL" | sudo tee -a /etc/sudoers', watchers=[init_sudopass])

    subprocess.run(['ssh-copy-id', 'chen@{}'.format(ip)])

    # Sshd
    c.run('sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak', watchers=[init_sudopass])
    # c.run('sed -i "s/#Port 22/Port 2112/g" /etc/ssh/sshd_config')
    # c.run('sed -i "s/PermitRootLogin yes/PermitRootLogin no/g" /etc/ssh/sshd_config')
    # c.run('sed -i "s/PasswordAuthentication yes/PasswordAuthentication no/g" /etc/ssh/sshd_config')
    c.run('sudo systemctl restart sshd', watchers=[init_sudopass])

    # Reconnect
    c = Connection(host=ip, user='chen', port='22')

    # Nginx
    c.run('sudo apt-get install nginx -y', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG www-data chen', pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable nginx', pty=True, watchers=[sudopass])
    #c.run('sudo mkdir /var/www/', pty=True, watchers=[sudopass]) # Huawei
    c.run('sudo chown chen:chen /var/www/ -R', pty=True, watchers=[sudopass])

    if ubuntu == '18.04':
        # 18.04
        c.run('sudo apt-get install software-properties-common -y', pty=True, watchers=[sudopass])
        c.run('sudo add-apt-repository universe', pty=True, watchers=[sudopass])
        c.run('sudo add-apt-repository ppa:certbot/certbot', pty=True, watchers=[sudopass])
        c.run('sudo apt-get update', pty=True, watchers=[sudopass])
    elif ubuntu == '19.10':
        # certbot ubuntu19.10
        c.run('sudo apt-get install certbot python-certbot-nginx -y',
              pty=True, watchers=[sudopass])

    # elif ubuntu == '20.04':
    else:
        c.run('sudo apt-get install snapd -y', pty=True, watchers=[sudopass])
        c.run('sudo snap install core', pty=True, watchers=[sudopass])
        c.run('sudo snap refresh core', pty=True, watchers=[sudopass])

        c.run('sudo snap install --classic certbot', pty=True, watchers=[sudopass])


    # docker
    # https://docs.docker.com/engine/install/ubuntu/
    c.run('sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common', pty=True, watchers=[sudopass])
    c.run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -', pty=True, watchers=[sudopass])
    c.run('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', pty=True, watchers=[sudopass])
    c.run('sudo apt-get update', pty=True, watchers=[sudopass])
    c.run('sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG docker chen', pty=True, watchers=[sudopass])

    # git
    c.run('sudo apt-get install git -y', pty=True, watchers=[sudopass])
    c.run('sudo groupadd git', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG git chen', pty=True, watchers=[sudopass])
    c.run('sudo mkdir /opt/git/', pty=True, watchers=[sudopass])
    c.run('sudo chown chen:git /opt/git -R', pty=True, watchers=[sudopass])

    # ufw
    c.run('sudo ufw default deny', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow 22/tcp', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow "Nginx Full"', pty=True, watchers=[sudopass])
    c.run('sudo ufw enable', pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable ufw', pty=True, watchers=[sudopass])
    c.run('sudo systemctl start ufw', pty=True, watchers=[sudopass])

@cli.command()
@click.argument('vps')
def install_snap(vps):
    """
    Install snap
    """
    c = Connection(vps)
    c.run('sudo apt-get install snapd -y', pty=True, watchers=[sudopass])
    c.run('sudo snap install core', pty=True, watchers=[sudopass])
    c.run('sudo snap refresh core', pty=True, watchers=[sudopass])

@cli.command()
@click.argument('vps')
def install_certbot(vps):
    """
    Install certbot by snap
    """
    c = Connection(vps)
    # c.run('sudo apt-get install snapd -y', pty=True, watchers=[sudopass])
    # c.run('sudo snap install core', pty=True, watchers=[sudopass])
    # c.run('sudo snap refresh core', pty=True, watchers=[sudopass])
    c.run('sudo snap install --classic certbot', pty=True, watchers=[sudopass])
    c.run('sudo ln -s /snap/bin/certbot /usr/bin/certbot', pty=True, watchers=[sudopass])



@cli.command()
@click.argument('vps')
def install_git(vps):
    """
    Install git
    """
    c = Connection(vps)
    c.run('sudo apt-get install git -y', pty=True, watchers=[sudopass])
    c.run('sudo groupadd git', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG git chen', pty=True, watchers=[sudopass])
    c.run('sudo mkdir /opt/git/', pty=True, watchers=[sudopass])
    c.run('sudo chown chen:git /opt/git -R', pty=True, watchers=[sudopass])

@cli.command()
@click.argument('vps')
def set_ufw(vps):
    """
    Set ufw config
    """
    c = Connection(vps)
    c.run('sudo ufw default deny', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow 22/tcp', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow "Nginx Full"', pty=True, watchers=[sudopass])
    c.run('sudo ufw enable', pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable ufw', pty=True, watchers=[sudopass])
    c.run('sudo systemctl start ufw', pty=True, watchers=[sudopass])


@cli.command()
@click.argument('vps')
def install_docker(vps):
    """
    安装Docker
    """
    c = Connection(vps)
    # docker
    # https://docs.docker.com/engine/install/ubuntu/
    # c.run('sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common', pty=True, watchers=[sudopass])
    # c.run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -', pty=True, watchers=[sudopass])
    c.run('sudo mkdir -p /etc/apt/keyrings', pty=True, watchers=[sudopass])
    c.run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg', pty=True, watchers=[sudopass])
    c.run('echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null', pty=True, watchers=[sudopass])

    c.run('sudo apt-get update', pty=True, watchers=[sudopass])
    # c.run('sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose', pty=True, watchers=[sudopass])
    c.run('sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG docker chen', pty=True, watchers=[sudopass])

@cli.command()
@click.argument('vps')
def install_nginx(vps):
    """
    """
    c = Connection(vps)
    # c.run('sudo apt-get install nginx -y', pty=True, watchers=[sudopass])
    # c.run('sudo usermod -aG www-data chen', pty=True, watchers=[sudopass])
    # c.run('sudo systemctl enable nginx', pty=True, watchers=[sudopass])
    # #c.run('sudo mkdir /var/www/', pty=True, watchers=[sudopass]) # Huawei
    # c.run('sudo chown chen:chen /var/www/ -R', pty=True, watchers=[sudopass])
    c.run('sudo apt-get install nginx -y', pty=True)
    # c.run('sudo usermod -aG www-data chen', pty=True)
    # c.run('sudo systemctl enable nginx', pty=True)
    # c.run('sudo chown chen:chen /var/www/ -R', pty=True)


@cli.command()
@click.argument('vps')
def install_php(vps):
    """
    安装PHP, MYSQL等
    """
    c = Connection(vps)
    #c.run('sudo apt-get install php-fpm', pty=True, watchers=[sudopass])
    c.run('sudo apt-get install mysql-server mysql-client', pty=True, watchers=[sudopass])
    c.run('sudo mysql_secure_installation', pty=True, watchers=[sudopass])


@click.command()
@click.option('--server', prompt='Server Name')
@click.option('--user', prompt='Server user')
def aws_init(server, user):
    """AWS服务器初始化
    """
    c = Connection(server)

    c.run('sudo apt update -y', pty=True, watchers=[sudopass])

    # Nginx
    c.run('sudo apt-get install nginx -y', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG www-data {}'.format(user),
          pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable nginx', pty=True, watchers=[sudopass])
    c.run('sudo chown {0}:{0} /var/www/ -R'.format(user),
          pty=True, watchers=[sudopass])

    c.run('sudo snap install --classic certbot', pty=True, watchers=[sudopass])

    # docker
    # https://docs.docker.com/engine/install/ubuntu/
    c.run('sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common', pty=True, watchers=[sudopass])
    c.run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -', pty=True, watchers=[sudopass])
    c.run('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', pty=True, watchers=[sudopass])
    c.run('sudo apt-get update', pty=True, watchers=[sudopass])
    c.run('sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG docker {}'.format(user),
          pty=True, watchers=[sudopass])

    # git
    c.run('sudo apt-get install git -y', pty=True, watchers=[sudopass])
    c.run('sudo groupadd git', pty=True, watchers=[sudopass])
    c.run('sudo usermod -aG git {}'.format(user),
          pty=True, watchers=[sudopass])
    c.run('sudo mkdir /opt/git/', pty=True, watchers=[sudopass])
    c.run('sudo chown {}:git /opt/git -R'.format(user),
          pty=True, watchers=[sudopass])

    # ufw
    c.run('sudo ufw default deny', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow OpenSSH', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow "Nginx Full"', pty=True, watchers=[sudopass])
    c.run('sudo ufw enable', pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable ufw', pty=True, watchers=[sudopass])
    c.run('sudo systemctl start ufw', pty=True, watchers=[sudopass])

@click.command()
@click.argument('ip')
@click.argument('user')
@click.argument('password')
@click.argument('ubuntu')
def fast(ip, user, password, ubuntu):
    """
    初始化服务器
    """
    c = Connection(host=ip, user=user, connect_kwargs={'password':password})
    c.run('apt-get update -y')
    c.run('groupadd chen')
    c.run('useradd -m -g chen -s /bin/bash chen')
    c.run('passwd chen')
    c.run('echo "chen ALL=(ALL:ALL) ALL" | tee -a /etc/sudoers')

    subprocess.run(['ssh-copy-id', 'chen@{}'.format(ip)])

    # Sshd
    c.run('cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak')
    # c.run('sed -i "s/#Port 22/Port 2112/g" /etc/ssh/sshd_config')
    c.run('sed -i "s/PermitRootLogin yes/PermitRootLogin no/g" /etc/ssh/sshd_config')
    c.run('sed -i "s/PasswordAuthentication yes/PasswordAuthentication no/g" /etc/ssh/sshd_config')
    c.run('systemctl restart sshd')

    # ufw
    c.run('sudo ufw default deny', pty=True, watchers=[sudopass])
    c.run('sudo ufw allow 22/tcp', pty=True, watchers=[sudopass])
    c.run('sudo ufw enable', pty=True, watchers=[sudopass])
    c.run('sudo systemctl enable ufw', pty=True, watchers=[sudopass])
    c.run('sudo systemctl start ufw', pty=True, watchers=[sudopass])




cli.add_command(initvps)
cli.add_command(aws_init)
cli.add_command(fast)
cli.add_command(install_docker)
cli.add_command(install_git)
cli.add_command(set_ufw)
cli.add_command(install_certbot)
cli.add_command(install_nginx)

if __name__ == '__main__':
    cli()
