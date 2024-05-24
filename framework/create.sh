

openssl genrsa -des3 -out private/ca_key.pem 4096
echo "create ca"
openssl req -x509 -new -nodes -key private/ca_key.pem -days 366 -sha256 -out private/ca_cert.pem

echo "write another ip for server :"
read IP

sudo cp private/ca_cert.pem /etc/ca-certificates/trust-source/anchors/
sudo update-ca-trust
sudo update-ca-certificates

echo "subjectAltName=DNS:localhost,IP:$IP" >> extfile.txt

openssl genrsa -out cert_key.pem 4096
echo "create csr"
openssl req -new -subj "/CN=localhost" -key cert_key.pem -out cert.csr
openssl x509 -req -days 3650 -in cert.csr -CA private/ca_cert.pem -CAkey private/ca_key.pem -out cert.pem -extfile extfile.txt -CAcreateserial

# so cert.pem is certificate for a server and cert_key.pem its a private key