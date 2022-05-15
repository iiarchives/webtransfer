# WebTransfer
#### a privacy-respecting file sharing service
---

### Frequently Asked Questions

*What is WebTransfer?*
> WebTransfer is a fast and free file sharing service designed to be privacy-respecting.

*Is WebTransfer public?*
> Yes! WebTransfer is publicly available [here](https://wt.iipython.cf).

*How much space does WebTransfer give you?*
> Each user gets a set amount of storage (by default, 6 gigabytes), and can upload files upto 2 gigabytes in size. After you upload a file, it expires in 24 hours to save storage space.

*Do I have to pay to use WebTransfer?*
> No. WebTransfer is and always will be completely free, no strings attached.

---

###  Design

WebTransfer is built on top of the Python Flask framework, utilizing public routes for HTML-serving pages and API routes for everything else. The frontend is designed using [Bootstrap](https://getbootstrap.com), [Bootstrap Icons](https://icons.getbootstrap.com), [JQuery](https://jquery.com) and AJAX.  

For example, when you load **/user/dashboard**, you get the dashboard HTML containing the template and a loading spinner. In the background, an AJAX request is made to **/user/api/files**, which populates the template and displays it.

---

###  Installation

Before you setup WebTransfer, you should have the following:
- Python 3.10+ ([download](https://python.org))
- Python Requirements (`python3 -m pip install -r reqs.txt`)
- Git SCM* ([download](https://git-scm.com))

If you built Python from source (Linux only):
- Python SQlite Extension (install sqlite libraries before building)
    - Debian: `sudo apt install libsqlite3-dev`
    - Fedora: `sudo dnf install sqlite-devel`

Begin setting up WebTransfer:
```bash
git clone https://github.com/ii-Python/webtransfer
cd webtransfer
python3 -m pip install -r reqs.txt
```

Before you attempt to launch WebTransfer, see [Configuration](#configuration) and then [Launching](#launching)

---

### Configuration

In order for Flask to use sessions properly, you require a secret key.  
To pass this to WebTransfer, either use the `SECRET_KEY` environment variable or use a `.env` file.  

> If you're using a `.env` file, place the following in it:
> `SECRET_KEY="hopefully a long and secure string"`

> If you're running via command line:
> `SECRET_KEY="hopefully a long and secure string" python3 ...`

Another **very** important thing to do is to switch to [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) if you plan on making your instance public.  
The built-in Werkzeug server will perform terribly compared to something as basic as [gunicorn](https://gunicorn.org).
- In the event that you do use gunicorn you could run the following:
- > python3 -m gunicorn -b 0.0.0.0:8080 -w 8 launch:app

---

### Launching

**Make sure you have enough space for uploads before you launch.**

To launch with the Werkzeug server:
> python3 launch.py

Preferably, to launch with Gunicorn:
> python3 -m gunicorn -b 0.0.0.0:8080 -w 8 launch:app
