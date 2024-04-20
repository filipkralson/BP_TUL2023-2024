import paramiko
import os

def upload_files_sftp(local_folder, remote_folder, server, username, private_key_path):
    try:
        # Create an SSH client instance
        client = paramiko.SSHClient()

        # Set the policy for automatically adding host keys
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load the private key for authentication
        private_key = paramiko.RSAKey(filename=private_key_path)

        # Connect to the SFTP server
        client.connect(server, username=username, pkey=private_key)

        # Open an SFTP session
        sftp = client.open_sftp()

        try:
            # List files in the local directory
            local_files = [f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]

            # Iterate through local files and upload them to the remote directory
            for local_file in local_files:
                local_file_path = os.path.join(local_folder, local_file)
                remote_file_path = os.path.join(remote_folder, local_file)

                # Upload the file to the remote directory
                sftp.put(local_file_path, remote_file_path)
                print(f"File {local_file} was successfully uploaded to {remote_folder}.")

        except Exception as e:
            # Handle exceptions during file upload
            print(f"Failure while uploading: {e}")

        finally:
            # Close the SFTP session and SSH client connection
            print("Closing connection...")
            sftp.close()
            client.close()
            print("Connection closed.")

    except Exception as e:
        # Handle exceptions during connection establishment
        print(f"Error: {e}")

# Example usage:
# upload_files_sftp('/path/to/local/folder', '/path/to/remote/folder', 'sftp.example.com', 'username', '/path/to/private/key')
