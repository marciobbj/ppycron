## PPyCron

Simple tool that allows users to manage cron jobs for Linux and Mac OS.

## Installing
Just type in the terminal:
```
pip install ppycron
```

## Usage
PPyCron lets you manage crontab entries in Unix-based environments. When instantiated, the package automatically creates a cron file if one isn’t available. Each cron job is associated with a unique identifier (UUID) so that you can reliably retrieve, edit, or delete specific jobs.

### Basic Example

#### Fetching Registered Crons
```python
In [1]: import ppycron

In [2]: crontab = ppycron.Crontab()

In [3]: crontab.get_all()
Out[3]: []
```

#### Adding a New Cron
When you add a new job, a unique ID is automatically generated:
```python
In [4]: job = crontab.add(interval="* * * * *", command="echo hello-world >> /var/log/crontab.log")
Out[4]: Cron(command='echo hello-world >> /var/log/crontab.log', interval='* * * * *', id='3f9c8bd2-1b67-4b78-8c4c-1e49b3f1a0c5')

In [5]: crontab.get_all()
Out[5]: [Cron(command='echo hello-world >> /var/log/crontab.log', interval='* * * * *', id='3f9c8bd2-1b67-4b78-8c4c-1e49b3f1a0c5')]
```

#### Editing an Existing Cron
Instead of searching by command, you now edit a job by its unique ID:
```python
In [6]: crontab.edit(cron_id=job.id, interval="*/10 * * * *", command="echo hello-world >> /var/log/crontab.log")
Out[6]: True

In [7]: crontab.get_all()
Out[7]: [Cron(command='echo hello-world >> /var/log/crontab.log', interval='*/10 * * * *', id='3f9c8bd2-1b67-4b78-8c4c-1e49b3f1a0c5')]
```

Now, if you check your crontab file:
```python
In [8]: import os
In [9]: os.system("crontab -l")
# Created automatically by Pycron =)
*/10 * * * * echo hello-world >> /var/log/crontab.log
```

#### Deleting an Existing Cron
Delete jobs using the job’s unique ID:
```python
In [10]: crontab.delete(cron_id=job.id)
Out[10]: True

In [11]: crontab.get_all()
Out[11]: []
```
