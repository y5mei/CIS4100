from collections import defaultdict


def buildCredentialDict(file_name: str = "S5-S3conf"):
    try:
        open(file_name, 'r')
    except FileNotFoundError:
        print("S5 Terminal can not find/read the file: ", file_name)
    file1 = open(file_name, 'r')
    lines = file1.readlines()
    d = defaultdict(lambda: None)

    for line in lines:
        strList = line.split("=")
        key = strList[0].replace(" ", "")
        if key == "aws_access_key_id":
            d[key] = strList[1].replace(" ", "").replace("\n", "")
        if key == "aws_secret_access_key":
            d[key] = strList[1].replace(" ", "").replace("\n", "")

        if d["aws_access_key_id"] and d["aws_secret_access_key"]:
            break

    if not d["aws_access_key_id"] or not d["aws_secret_access_key"]:
        raise Exception("Didn't get the credentials from the file: ".file_name)
    else:
        return d



if __name__ == '__main__':
    mydict = buildCredentialDict("S5-S3conf")
    mylist = list(mydict.items())
    print(mylist)
