import socket
import dns.resolver
import os
import platform


def get_hostname_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")

def get_dns_records(domain):
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'PTR']
    resolver = dns.resolver.Resolver()

    for record in record_types:
        try:
            answers = resolver.resolve(domain, record)
            print(f"{record} Records:")
            for rdata in answers:
                print(f"  {rdata}, {rdata.to_text()}")

        except dns.resolver.NXDOMAIN:
            print(f"{domain} does not exist.")
        except dns.resolver.Timeout:
            print(f"Query timed out.")
        except dns.resolver.NoAnswer:
            print(f"No answer for {record} record.")
        except Exception as e:
            print(f"Error: {e}")

def main():
    print("Hostname Information:")
    get_hostname_info()

    for domain in [".", "cloud", "scw.cloud", "nl-ams.scw.cloud"]:
        print("\nDNS Records:", domain)
        get_dns_records(domain)

if __name__ == "__main__":
    with open("/etc/resolv.conf", "r") as f:
        data = f.read()
        print(data)
    main()