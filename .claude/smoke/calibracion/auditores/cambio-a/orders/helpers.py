from .models import STATUS_CHOICES


def status_label(code):
    labels = {}
    for value, label in STATUS_CHOICES:
        labels[value] = label
    if code in labels:
        return labels[code]
    return code
