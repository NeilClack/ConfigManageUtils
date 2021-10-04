import boto3
import base64
from flask import current_app


def redacted(data: list) -> list:
    """
    Replace the key "value" of a dictionary object with "REDACTED", if the dictionary contains a "secret":"True" key:value pair

    Parameters
    ----------
    data: List of dictionaries to check and update

    Response
    --------
    List of dictionaries as provided with the replaced value "REDACTED"
    """
    for i in data:
        if i["secret"]:
            i["value"] = "REDACTED"

    return data


def prefix_names(data: list) -> list:
    """
    Combine the prefix and the name of a each dictionary in a list

    Parameters
    ----------
    """
    for param in data:
        param["name"] = "/" + param["prefix"] + "/" + param["name"]
    return data


def enc(data: str) -> str:
    """
    Encrypts the given string data with AWS KMS

    Parameters
    ----------
    data: String to encrypt

    Response
    --------
    String
    """
    kms = boto3.client("kms")
    res = kms.encrypt(
        KeyId=current_app.config["KMS_KEY_ID"],
        Plaintext=data,
        EncryptionAlgorithm="SYMMETRIC_DEFAULT",
    )
    enc_data = base64.b64encode(res["CiphertextBlob"])
    enc_data = enc_data.decode("ascii")
    return enc_data


def dec(data: str) -> str:
    """
    Decrypts an encrypted string with AWS KMS

    Parameters
    ----------
    data: String to decrypt: Ensure this is an encrypted string and not a raw string or encoding will break.

    Response
    --------
    String
    """
    data = base64.b64decode(data)
    kms = boto3.client("kms")
    res = kms.decrypt(CiphertextBlob=data)
    dec_bytes = res["Plaintext"]
    return dec_bytes.decode("ascii")


def store_ps(data: list) -> list:
    """
    Stores data in AWS Parameter store under SSM

    Parameters
    ----------
    data: List of dictionaries representing parameters to store

    Response
    --------
    List of AWS SSM responses as dictionaries for each parameter stores.
    """
    ssm = boto3.client("ssm")

    response_list = []

    for param in data:
        param.pop("prefix")
        if param["secret"]:
            print(param["value"])
            param["value"] = dec(param["value"])

            res = ssm.put_parameter(
                Name=param["name"],
                Value=param["value"],
                Description=param["comment"],
                Type="SecureString",
                KeyId=current_app.config["KMS_KEY_ID"],
                Overwrite=True,
            )
            response_list.append(res)
        else:
            res = ssm.put_parameter(
                Name=param["name"],
                Value=param["value"],
                Description=param["comment"],
                Type="String",
                Overwrite=True,
            )
            response_list.append(res)

    return response_list
