# iCIMS safety boundary

The adapter never bypasses CAPTCHA or anti-bot controls, enters MFA or verification codes, creates candidate accounts, answers employer assessments, attests legal declarations, completes demographic self-identification, or invents unknown answers.

Dry runs never activate final Submit. A live outcome may be `submitted` only when confirmation-kind evidence is observed. Credential evidence contains only the selected external profile name, never credential values.
