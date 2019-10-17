

def free_text(description, current):
    x = ""
    print("  " + description + " : " + current)
    x = input("   (blank to keep existing): ")
    if x == "":
        return current
    else:
        return x


def choice(description, current, values):
    x = ""
    print("  " + description + " [" + "|".join(values) + "] : " + current)
    while x not in values:
        x = input("   (blank to keep existing): ")
        if x == "":
            x = current
    return x

def patterns_list(description, current):
    retval = []
    x = ""
    print("  " + description + ": " + ", ".join(current))
    x = input("   (blank to keep existing): ")
    if x == "":
        return current
    else:
        retval.append(x)
        while x != "":
            x = input("   (blank when finished): ")
            if x != "":
                retval.append(x)
        return retval




