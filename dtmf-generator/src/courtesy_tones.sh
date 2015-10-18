. ./send_dtmf.sh

use_cw=false
if ${use_cw}; then
    send_dtmf *7109931 R1T1-CT-D
    send_dtmf *7119952 R1T2-CT-K
    send_dtmf *7129953 R2T1-CT-L
    send_dtmf *7139932 R2T2-CT-E
else
    #t1=0512051505190522

    # DADG
    t1=0522051705100503

    # F# D F# D
    #t2=0514051005140510

    # CGEC
    #20 15 12 8
    t2=0520051505120508

    # ADAD
    # 17 22 17 10

    send_dtmf *710${t1} "Courtesy tone DADG"
    send_dtmf *711${t2} "Courtesy tone CGEC"
    send_dtmf *712${t1} "Courtesy tone DADG"
    send_dtmf *713${t2} "Courtesy tone CGEC"
fi