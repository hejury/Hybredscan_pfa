from oletools.mraptor import MacroRaptor
def mraptor_scan(filepath):
    mraptor = MacroRaptor(filepath)
    mraptor.scan()
    return {
        "contains_macros": mraptor.matches,
        "is_suspicious": mraptor.suspicious,
    }