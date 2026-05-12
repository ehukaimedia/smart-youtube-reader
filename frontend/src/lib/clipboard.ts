export function copyText(text: string, onCopied: () => void) {
    const fallbackCopy = () => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        onCopied();
    };

    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(onCopied).catch(fallbackCopy);
        return;
    }

    fallbackCopy();
}
