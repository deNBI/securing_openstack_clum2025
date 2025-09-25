# Securing a Web Service in OpenStack: A Hands-On Workshop
---

This workshop is a practical guide to **securing a web service** in the de.NBI Berlin OpenStack environment. You'll learn how to expose a service to the internet safely, using a **reverse proxy**, **load balancer**, and **firewall rules**, complemented by **SSL/TLS encryption** and **authentication**.

### What We'll Cover

* **Network Setup**: Configure a secure network architecture using the OpenStack graphical user interface.
* **Virtual Machines & Docker**: Create and set up virtual machines to host a simplified, containerized web service.
* **Reverse Proxy**: Implement a Dockerized reverse proxy to manage **HTTP/S encryption** and **authentication**.
* **Automated HTTPS**: Discover the key mechanisms to achieve automated SSL/TLS certificates for your service.

This workshop emphasizes hands-on application and best practices for securing your own cloud-based web services. We will delve into more detailed topics and questions as time permits.

***

### Key Concepts

* **Load Balancer**: A device or service that efficiently distributes incoming network traffic across a group of backend servers. Its purpose is to increase the capacity, reliability, and availability of an application.
* **Reverse Proxy**: A server that sits in front of one or more web servers, forwarding client requests to those servers. It acts as a single point of entry, providing an extra layer of security, and can handle tasks like **SSL/TLS encryption** and caching.
* **SSL/TLS**: Stands for Secure Sockets Layer / Transport Layer Security. These are cryptographic protocols that provide secure communication over a computer network. They are essential for encrypting data sent between a user's browser and a web server, protecting it from eavesdropping and tampering.
* **HTTPS**: Stands for Hypertext Transfer Protocol Secure. It is the secure version of HTTP, the protocol used to send data between a web browser and a website. The 'S' at the end of HTTPS stands for 'Secure', meaning all communications between your browser and the website are encrypted via SSL/TLS.
* **Authentication**: The process of verifying the identity of a user, service, or device. It ensures that only authorized parties can access a system or resource. We'll explore methods like **BasicAuth** and **O2AUTH** to control access to our web service.

---

### Technologies Used

| Tool/Technology | Description |
| :--- | :--- |
| **OpenStack** | A suite of open-source software for creating and managing private and public clouds. In this workshop, we'll use it to provision our virtual machines, networks, and security rules. |
| **OpenStack Octavia** | The native load-balancing-as-a-service component of OpenStack. We'll use it to distribute incoming traffic and route it to our reverse proxy. |
| **Docker** | A platform for developing, shipping, and running applications in containers. We'll use it to package our web service and reverse proxy, ensuring they are portable and easy to manage. |
| **Python HTTP Server** | A simple web server written in Python. This will be our "dummy" web service to demonstrate the security principles. |
| **Caddy** | An open-source web server with powerful reverse proxy capabilities. We'll use it for its built-in automation of HTTPS certificate provisioning via Let's Encrypt. Caddy simplifies SSL/TLS encryption, making it easy to secure web traffic. |

---

### Prerequisites

* [ ] Everyone has access to the OpenStack project "CLUM2025SecWeb1".
* [ ] Everyone has added a Public SSH Key to the OpenStack environment for remote access.
* [ ] Everyone can clone the workshop's GitHub repository.

---

### Step 1: Network and Security Group Setup 🌐

Before deploying our VMs, we will create a network infrastructure suitable for a secure setup. This involves two key networks and their associated security groups.

#### Network Setup

* **`dmz-internal` Network**: A network with a subnet that connects to the default router and the external floating IP pool, allowing our Octavia Load Balancer to receive internet traffic.
* **`webservice-network`**: An internal network and subnet that will host our web service and reverse proxy VMs. This network is isolated from direct public access.

#### Security Groups (Firewall)

We will configure two separate Security Groups to act as our firewalls:

* **`ReverseProxy-SecGroup`**: This group handles inbound traffic from the load balancer to the reverse proxy. It will be configured to allow ingress on ports **80 (HTTP)** and **443 (HTTPS)**.
* **`Webservice-SecGroup`**: This group controls traffic from the reverse proxy to the internal web service. For example, if our service listens on port `8080`, this group will allow ingress on that port.

---

### Step 2: Deploying the Virtual Machines 🚀

Now we will launch two virtual machines (VMs) and connect them to our private network and corresponding security groups.

#### **Reverse Proxy VM**

* **Name:** `reverse-proxy`
* **Network:** `webservice-network`
* **Security Group:** `ReverseProxy-SecGroup`
* **Flavor:** Choose a small flavor (e.g., `m1.small`).
* **Image:** Use a recent Ubuntu image (e.g., `Ubuntu 22.04 LTS`).
* **Key Pair:** Select the SSH key pair you added as a prerequisite.

#### **Web Service VM**

* **Name:** `web-service`
* **Network:** `webservice-network`
* **Security Group:** `Webservice-SecGroup`
* **Flavor:** Choose a small flavor (e.g., `m1.small`).
* **Image:** Use a recent Ubuntu image (e.g., `Ubuntu 22.04 LTS`).
* **Key Pair:** Select the SSH key pair you added as a prerequisite.

After launching the instances, you can find their internal IP addresses on the OpenStack dashboard. Note these down, as you'll need them later.

---

### Step 3: Creating the Octavia Load Balancer

The load balancer is our entry point from the internet. It will distribute traffic to our reverse proxy VM.

1.  **Create a Load Balancer**: In the OpenStack dashboard, navigate to **Network > Load Balancers** and click **Create Load Balancer**.
    * **Name:** `workshop-lb`
    * **Subnet:** Select the `dmz-internal` subnet. This is crucial as it connects the load balancer to the public network.
    * **Floating IP:** Attach a new or existing floating IP to the load balancer. This will be the public IP address of your web service.

2.  **Add a Listener**: A listener defines the protocol and port on which the load balancer listens for incoming traffic.
    * Select the `workshop-lb` load balancer and go to the **Listeners** tab. Click **Add Listener**.
    * **Name:** `http-listener`
    * **Protocol:** `HTTP`
    * **Port:** `80`
    * **Default Pool:** Create a new pool called `http-pool`.

3.  **Configure the Pool**: A pool is a group of backend servers (in our case, the reverse proxy VM) that will handle the traffic.
    * After creating the listener, you'll be prompted to configure the pool.
    * **Protocol:** `HTTP`
    * **Load Balancing Method:** `ROUND_ROBIN`
    * **Health Monitor:** Create a `HTTP` health monitor to check if the reverse proxy is up and running.
        * **Type:** `HTTP`
        * **Delay:** `5` (seconds)
        * **Timeout:** `3` (seconds)
        * **Max Retries:** `3`

4.  **Add Members to the Pool**: Finally, add your `reverse-proxy` VM as a member of the pool.
    * Navigate to the `http-pool` and click **Add Member**.
    * **IP Address:** Enter the internal IP address of your `reverse-proxy` VM.
    * **Port:** `80` (The reverse proxy will be configured to listen on this port).

5.  **Repeat for HTTPS**: Follow the same steps to create a second listener for HTTPS traffic.
    * **Listener Name:** `https-listener`
    * **Protocol:** `TERMINATED_HTTPS` (This offloads the SSL/TLS encryption to the load balancer, which is a common practice).
    * **Port:** `443`
    * **Certificate:** You will need to upload a security certificate for this.
    * **Default Pool:** Create a new pool called `https-pool`. Add the `reverse-proxy` VM as a member with port `443`.

Now, your load balancer is configured to receive internet traffic on its floating IP and forward it to your reverse proxy VM, providing a secure and scalable entry point for your web service.

---

### Step 4: Configuring and Deploying the Services 💻

We will now configure our VMs to run the web service and the reverse proxy using Docker.

1.  **Clone the GitHub Repository**:
    * SSH into both the `web-service` and `reverse-proxy` VMs.
    * On each VM, clone the workshop repository containing the Docker files:
        ```bash
        git clone [https://github.com/your-github-repo-url.git](https://github.com/your-github-repo-url.git)
        cd your-github-repo-name
        ```

2.  **Deploy the Web Service**:
    * On the `web-service` VM, navigate to the directory with the `docker-compose.yml` file for the web service.
    * Start the web service container:
        ```bash
        docker compose up -d
        ```
    * **Test the connection**: From the `reverse-proxy` VM, use `curl` to verify that you can reach the web service on its internal IP address.
        ```bash
        curl http://<web-service-internal-ip>:8080
        ```
        You should receive a response from the web service.

3.  **Deploy the Reverse Proxy**:
    * On the `reverse-proxy` VM, navigate to the directory with the Caddy Docker files.
    * **Adapt the Caddyfile**: Open the `Caddyfile` and replace the placeholder with the **internal IP address** of your `web-service` VM.
    * Start the reverse proxy container:
        ```bash
        docker compose up -d
        ```
    * **Check the Caddy logs**: View the logs to confirm that Caddy has successfully obtained an SSL/TLS certificate from Let's Encrypt.
        ```bash
        docker logs caddy-container-name
        ```
        Look for messages indicating successful certificate acquisition.
    * **Test the connection**: From the `web-service` VM, use `curl` to test the reverse proxy.
        ```bash
        curl https://<reverse-proxy-internal-ip>

# Deploying FastAPI with docker

For vm docker-app

* prepare FastAPI
 
To deploy FastAPI with docker we firstly must create all needed directories and files for FastAPI. This includes the python files and a text file with the required apps from pip for FastAPI.

Create the directories and child folders.
```console
mkdir -p ~/compose/web-app/app
```

Write an empty python file called ```~/compose/web-app/app/__init__.py```.

```console
touch ~/compose/web-app/app/__init__.py
```

Than create another file ```~/compose/web-app/app/main.py``` with the following content:

```python
from typing import Union

from fastapi import FastAPI

import os

hostname = os.environ['HOST_NAME']

app = FastAPI(root_path="/p/"+hostname+"/80")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
```

This will import the fastapi python module and use it to create a new object called ```app```. In this environment we need to use the host name of the vm to reach the API with the browser. Therefor the root directory is set to a value build with the hostname from the vm. To use the environmental variable it needs to be exported:

```console
export HOSTNAME
```

When the root directory is called the key value pair ```"Hello": "World``` should be given back. The items can be called with the ```item_id```. 

Now create a file with the dependencies for the app you want to use. In this case we need three apps from pip. Create the file ```~/compose/web-app/requirements.txt```:

```text
fastapi>=0.68.0,<0.69.0
pydantic>=1.8.0,<2.0.0
uvicorn>=0.15.0,<0.16.0
```
This file will be used later to install all necessary program for the app. The numbers after the names define which version will be installed.

* Deploy the app with docker

To deploy FastAPI with docker we need a ```Dockerfile``` in the folder ```~/compose/web-app/Dockerfile```. 

```Dockerfile
FROM python:3.9
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

This will use the python image in version 3.9 to create a container in which the directory ```code``` is created. The ```code``` directory is defined as default or *working directory*, all actions are done there.
The file with the required programs is copied to the folder and used to install all inserted programs with ```pip install```.
Now the folder ```app``` with the files ```__init__.py``` and ```main.py``` is copied to the *working directory*.
The last line calls the command ```uvicorn app.main:app --host 0.0.0.0 --port 80``` in the container.

Next we need to create an image from the ```Dockerfile```. Note the path at the end of this command, indicating the location of the ```Dockerfile```
```console
sudo docker build -t myimage compose/web-app/
```

When the image build is done we can start a container using this image and a environmental variable used in the ```~compose/web-app/app/main.py``` file.
```console
sudo docker run -e HOST_NAME=$HOSTNAME -d --name mycontainer -p 80:80 myimage
```

The content can be checked with a web browser by using the external IP of the machine an d port 80.
To terminate the container and delete the image use the following commands:

```console
sudo docker stop mycontainer
sudo docker rm mycontainer
sudo docker rmi myimage
```

# Deploying reverse proxy with docker

For vm docker-nginx

* preparation of reverse proxy

To deploy the reverse-proxy with docker we firstly must create the directories and the config file for nginx.

Create the directories and child folders.
```console
mkdir -p ~/compose/proxy
```

Create the file ```~/compose/proxy/conf``` with the following content:
```conf
server {
  listen 80;
  server_name compose-reverse-proxy-1;
  location / {
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-NginX-Proxy true;
    proxy_pass http://<ip_from_docker-app>:8080;
    proxy_ssl_session_reuse off;
    proxy_set_header Host $http_host;
    proxy_cache_bypass $http_upgrade;
    proxy_redirect off;
  }
}
```
 
This file will be used for a simple reverse-proxy that redirects all incoming traffic to the ip of the web-service vm at port 8080 and use some security measures for the connection. Fill in the ip of your ```docker-app``` vm.

* deploy the reverse proxy with docker

Now create a Dockerfile in ```~/compose/proxy/Dockerfile``` and add the following content:
```Dockerfile
FROM nginx:1.13-alpine
COPY conf /etc/nginx/conf.d/default.conf
```

This will load the image nginx in version 1.13-alpine for the reverse proxy and copy the previously created ```conf``` file to the container.


# Deploy FastAPI with docker compose

For vm docker-app

* Preparation of FastAPI 

We need to change the existing ```~/compose/web-app/Dockerfile``` for FastAPI so we can use a reverse proxy.

Add the tag ```--proxy-headers``` to the issued command in the last line and change the port to ```8080```. The new file should look like this:
```Dockerfile
FROM python:3.9
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8080"]
```

To use the port 8080 with FastAPI we also need to change the ```~/compose/web-app/app/main.py``` file to use the changed url as root path. You need to change the creator for the FastAPI app in the file and edit the root path to ```"/p/+hostname+"/8080"``` 

```python
from typing import Union

from fastapi import FastAPI

import os

hostname = os.environ['HOST_NAME']

app = FastAPI(root_path="/p/"+hostname+"/8080")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
```


* prepare docker compose for FastAPI

We can use the previously created folders and both ```Dockerfiles``` for the docker compose deployment. 

To use docker compose, create a ```docker-compose.yml``` file in the directory ```~/compose/docker-compose.yml``` and enter the following:

```yml
version: "3.8"
services:
  web-app:
    build: ./web-app
    network_mode: "host"
    environment:
      HOST_NAME: $HOSTNAME
```

The version is just for reference it is not used to determine the docker version in use. In the section ```services:``` the containers to run are specified. 
In the ```build:``` tag of each service the folder for the Dockerfile is specified. As the ```docker-compose.yml``` file is located in the directory ```~/compose``` the folders to the Dockerfile is given in accordance to the directory of the ```docker-compose.yml``` file, indicated by the ```.``` at the beginning. 

In the section ```environment``` the variable for the vm host name is passed to the container. In the section ```networks:``` a network is created. We call it ```app-net:``` with the parameter ```ipam:``` we create a subnet for the containers with an usable ip range of 10.0.32.0/28. Select the default driver and an appropriate subnet (Default docker and docker compose networks are in the range of the OpenStack training public2 range and therefore can not be used.)

This will create one container from the folder ```~compose/web-app/``` which we just created. For the container the corresponding ```Dockerfile``` will be used. 

To use the environmental variable export it:

```console
export HOSTNAME
```

To start the container change to directory in which the ```~/compose/docker-compose.yml``` is located and run the following command:
```console
docker compose up
```

# Deploy reverse proxy with docker compose

For vm docker-nginx

* prepare docker compose for nginx

We can use the previously created folders and both ```Dockerfiles``` for the docker compose deployment. 

To use docker compose, create the file ```~/compose/docker-compose.yml``` and enter the following:

```yml
version: "3.8"
services:
  proxy:
    build: ./proxy
    network_mode: "host"
```

Then start the containers with the following command:
```
docker compose up
```

Use your browser to reach the IP of the vm and you should see the FastAPI page.

## Connect the vms

Both services should be ready to use, as the web-service is listening on the host port 8080 and the reverse-proxy is forwarding all requests to the web-service on port 8080.
