# Securing a Web Service in OpenStack: A Hands-On Workshop
---

This workshop is a practical guide to **securing a web service** in the de.NBI Berlin OpenStack environment. You'll learn how to expose a service to the internet safely, using a **reverse proxy**, **load balancer**, and **firewall rules**, complemented by **SSL/TLS encryption** and **authentication**.

### What We'll Cover

* **Network Setup**: Configure a secure network architecture using the OpenStack graphical user interface.
* **Virtual Machines & Docker**: Create and set up virtual machines to host a simplified, containerized web service.
* **Reverse Proxy**: Implement a Dockerized reverse proxy to manage **HTTP/S encryption** and **authentication**.
* **Automated HTTPS**: Discover the key mechanisms to achieve automated SSL/TLS certificates for your service.

This workshop emphasizes hands-on application and best practices for securing your own cloud-based web services. We could dive into more detailed topics and questions as time permits.

***

### Key Concepts

* **Load Balancer**: A device or service that efficiently distributes incoming network traffic across a group of backend servers. Its purpose is to increase the capacity, reliability, and availability of an application.
* **Reverse Proxy**: A server that sits in front of one or more web servers, forwarding client requests to those servers. It acts as a single point of entry, providing an extra layer of security, and can handle tasks like **SSL/TLS encryption** and caching.
* **SSL/TLS**: Stands for Secure Sockets Layer / Transport Layer Security. These are cryptographic protocols that provide secure communication over a computer network. They are essential for encrypting data sent between a user's browser and a web server, protecting it from eavesdropping and tampering.
* **HTTPS**: Stands for Hypertext Transfer Protocol Secure. It is the secure version of HTTP, the protocol used to send data between a web browser and a website. The 'S' at the end of HTTPS stands for 'Secure', meaning all communications between your browser and the website are encrypted via SSL/TLS.
* **Authentication**: The process of verifying the identity of a user, service, or device. It ensures that only authorized parties can access a system or resource. We'll explore methods like **BasicAuth** and maybe **O2AUTH** to control access to our web service.

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

* **`CLUM2025SecWeb-dmz-int-network` Network**: A network with a subnet that connects to the dmz-router ``CLUM2025SecWeb-dmz-router`` and the external floating IP pool ``dmz``, allowing our Octavia Load Balancer to receive internet traffic adn redirect internally to the reverse-proxy VM.
* **`CLUM2025SecWeb1-network-2`**: An internal network and subnet that connects to the public-router ``CLUM2025SecWeb1-router-2`` and the external floating IP pool ``public``, allowing our VM's to access the internet and be accessable via the User-Jumphost for remote-access. This network is isolated from direct public access network ``dmz``.

#### Security Groups (Firewall)

We will configure two separate Security Groups to act as our firewalls:

* **`ReverseProxy-SecGroup-<YOUR_NAME>`**: This group handles inbound traffic from the load balancer to the reverse proxy. It will be configured to allow ingress on ports **80 (HTTP)** and **443 (HTTPS)**. Granularity is recommended (e.G. just allow the loadbalancer to access the reverse-proxy VM)
* **`Webservice-SecGroup-<YOUR_NAME>`**: This group controls traffic from the reverse proxy to the internal web service. For example, if our webservice listens on port `8080`, this group will allow ingress on that port. Granularity is recommended (e.G. just allow the reverse-proxy to access the webservice VM)

---

### Step 2: Deploying the Virtual Machines 🚀

Now we will launch two virtual machines (VMs) and connect them to our private network and corresponding security groups.

#### **Reverse Proxy VM**

* **Name:** `reverse-proxy-<YOUR_NAME>`
* **Network:** `CLUM2025SecWeb1-network-2`
* **Security Group:** `ReverseProxy-SecGroup-<YOUR_NAME>` , `default`
* **Flavor:** `de.NBI default`
* **Image:** `Ubuntu-24.04-Docker`
* **Key Pair:** Select the SSH key pair you added as a prerequisite

#### **Web Service VM**

* **Name:** `web-service-<YOUR_NAME>`
* **Network:** `CLUM2025SecWeb1-network-2`
* **Security Group:** ``Webservice-SecGroup-<YOUR_NAME>` , `default`
* **Flavor:** `de.NBI default`
* **Image:** `Ubuntu-24.04-Docker`
* **Key Pair:** Select the SSH key pair you added as a prerequisite.

After launching the instances, you can associate a floating-ip from the pool `public` to your VMs to have remote-access.

---

### Step 3: Creating the Octavia Load Balancer

The load balancer is our entry point from the internet. It will distribute traffic to our reverse proxy VM.

1.  **Create a Load Balancer**: In the OpenStack dashboard, navigate to **Network > Load Balancers** and click **Create Load Balancer**.
    * **Name:** `workshop-lb-<YOUR_NAME>`
    * **Subnet:** Select the `CLUM2025SecWeb-dmz-int-network` subnet. This is crucial as it connects the load balancer to the public network.
    * **Floating IP:** Attach an existing and predefined floating-ip from the pool `dmz` to your load balancer. This will be the public IP address of your web service and is connected to the dns-entry.

2.  **Add a Listener**: A listener defines the protocol and port on which the load balancer listens for incoming traffic.
    * Select the `workshop-lb` load balancer and go to the **Listeners** tab. Click **Add Listener**.
    * **Name:** `http-listener`
    * **Protocol:** `TCP`
    * **Port:** `80`
    * **Default Pool:** Create a new pool called `http-pool`.

3.  **Configure the Pool**: A pool is a group of backend servers (in our case, the reverse proxy VM) that will handle the traffic.
    * After creating the listener, you'll be prompted to configure the pool.
    * **Protocol:** `TCP`
    * **Load Balancing Method:** `ROUND_ROBIN`
    * **Health Monitor:** Create a `HTTP` health monitor to check if the reverse proxy is up and running.
        * **Type:** `TCP`
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
        git clone https://github.com/deNBI/securing_openstack_clum2025.git
        cd /securing_openstack_clum2025
        ```

      **Repository tree view**
      ```
      ├── Docker/
      │   ├── proxy/
      │   │   ├── caddy_basicauth/
      │   │   │   ├── Dockerfile
      │   │   │   ├── docker-compose.yml
      │   │   │   └── Caddyfile
      │   │   └── caddy_oauth2/
      │   │       ├── Dockerfile
      │   │       ├── docker-compose.yml
      │   │       └── Caddyfile
      │   └── web-app/
      │       ├── python-webserver/
      │       │   ├── Dockerfile
      │       │   ├── docker-compose.yml
      │       │   └── server.py
      │       └── fast-api/
      │           ├── Dockerfile
      │           ├── docker-compose.yml
      │           └── requirements.txt
      └── README.md
      ```

2.  **Deploy the Web Service**:
    * On the `web-service` VM, navigate to the directory `./Docker/web-app/python-webserver` with the `docker-compose.yml` file for the web service.
    * Check the exposed ports in the `docker-compose.yml` and `server.py`. The preconfigured port is `8080`. You could adapt it if you want to but dont forget you need to adapt the reverse-proxy aswell as the SecGroups
      
      **docker-compose.yml**
      ```
      services:
         web_server:
           build: .
           container_name: python_web_server
           ports:
             - "8080:8080"
      ```
      **server.py**
      ```
      from http.server import HTTPServer, BaseHTTPRequestHandler
      import socketserver

      class S(BaseHTTPRequestHandler):
          def do_GET(self):
              self.send_response(200)
              self.send_header('Content-type', 'text/html')
              self.end_headers()
              self.wfile.write(b'Welcome to CLUM 2025 Secure a Webservice')
      
      if __name__ == "__main__":
          PORT = 8080
          Handler = S
          httpd = socketserver.TCPServer(("", PORT), Handler)
          print("serving at port", PORT)
          httpd.serve_forever()
      ```
    * Start the web service container:
        ```bash
        sudo docker compose up -d
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
        sudo docker compose up -d
        ```
    * **Check the Caddy logs**: View the logs to confirm that Caddy has successfully obtained an SSL/TLS certificate from Let's Encrypt.
        ```bash
        sudo docker logs caddy-container-name
        ```
        Look for messages indicating successful certificate acquisition.
    * **Test the connection**: From the `web-service` VM, use `curl` to test the reverse proxy.
        ```bash
        curl https://<reverse-proxy-internal-ip>

## Connect the vms

Both services should be ready to use, as the web-service is listening on the host port 8080 and the reverse-proxy is forwarding all requests to the web-service on port 8080.
