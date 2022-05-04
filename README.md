## PPyCron

Simple tool that allows users to manage cron jobs for Linux.


## Installing
One should just type in the terminal: 
```
pip install ppycron
```

## Usage
PPyCron will let you manage crontabs in Unix based environments. When instantiated
the package will automatically create a cron file if it is not available. 

### Basic Example
#### Fetching crons registered
```
In [1]: import ppycron

In [2]: crontab = ppycron.Crontab()

In [3]: crontab.get_all()
Out[3]: []
```
#### Adding new Cron
```
In [4]: crontab.add(interval="* * * * *", command="echo hello-world >> /var/log/crontab.log")
Out[4]: Cron(command='echo hello-world >> /var/log/crontab.log', interval='* * * * *')

In [5]: crontab.get_all()
Out[5]: [Cron(command='echo hello-world >> /var/log/crontab.log', interval='* * * * *')]
```

#### Editing some existing cron
We fetch the cron by its command:

```
In [6]: crontab.edit(interval="*/10 * * * *", cron_command="echo hello-world >> /var/log/crontab.log")
Out[6]: True

In [7]: crontab.get_all()
Out[7]: [Cron(command='echo hello-world >> /var/log/crontab.log', interval='*/10 * * * *')]
```

If you check your crontab file you will see
```
In [9]: os.system("crontab -l")
# Created automatically by Pycron =)
*/10 * * * * echo hello-world >> /var/log/crontab.log
```

#### Deleting existing crons
```
In [10]: crontab.delete("echo hello-world >> /var/log/crontab.log")
Out[10]: True

In [11]: crontab.get_all()
Out[11]: []
```
