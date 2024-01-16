import jfkpay.orders as orders

mail_data = [
    {'name': 'Delivered-To', 'value': 'foo@gmail.com'},
    {'name': 'Received', 'value': 'by 2002:a17:906:cd05:b0:a2c:7175:f358 with SMTP id oz5csp2292325ejb;        Mon, 15 Jan 2024 04:02:00 -0800 (PST)'},
    {'name': 'X-Google-Smtp-Source', 'value': 'AGHT+IHQ6QTMelhyX2zJupxvJpuJ24u3iNTtmDLCl1FBZ5aH/wAfznGkfXd9+h3QDWCEysNnLnzT'},
    {'name': 'X-Received', 'value': 'by 2002:a05:6402:308e:b0:558:f4d6:e8d5 with SMTP id de14-20020a056402308e00b00558f4d6e8d5mr1552297edb.28.1705320120436;        Mon, 15 Jan 2024 04:02:00 -0800 (PST)'},
    {'name': 'ARC-Seal', 'value': 'i=1; a=rsa-sha256; t=1705320120; cv=none;        d=google.com; s=arc-20160816;        b=IVE5+xjH8Jc8m2HxgL3jqyHmYLLMheoMcgS/rNdRfvjuZ8q47mmCKw1kqtAzCllmos         I2NI02T/kxShfKiq3YzAC3fXHdYN36gn1WZQwDMxQmWfmg63iKpSTwY00T+xRWSbx/fb         FdBLQFLt5OSXuy6tVdcV8ZDLGLpmE3RbgQPtXwsaQ5V/9EYnzzolRVoHvAYmM0qC51v9         CZXOMNpLTchTziZnOj+UESHgcsmjxoWNGrMcll1c2TnKRByjMHjtwIDt5ADzxkryF3vm         7hkKHsXB72D4BJuxFrDNKXsL3LtOD13tU9WDvLdjKxqCVLC2w0luCTacYQ6aOn/iDUIg         /NyQ=='},
    {'name': 'ARC-Message-Signature', 'value': 'i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;        h=reply-to:from:mime-version:subject:message-id:to:date         :dkim-signature;        bh=ocxOKY2H4lwO3ngeE/nq0tz+mZd9+11KitrkNq3u/U4=;        fh=uIUq0yZ4wMK5DthHe7Cg+q6INAZ4DY6B4RFtMNrI/Lk=;        b=s2LAYObbMXIaNVdaupFhodO2voiHtUPBcxPWbsLbiDYz3YBmlra6I0ETkcOnJ3goiy         EZQ3TqyibqjUo6lucfYrREzdAjkYzxJrFHSmMUEcp3329uyx/X/cXyQJ2+zf4SUPSIr/         Br3Iw0zYYZYjfd+omK5wgM/DZl0cXGH0bfiyTHj/8VzZ8fuLNrijyOZxic96B6qVCfRW         lMyE+16iIL+ephMYr0nkDl6RYT3Dwi8JDMBhaJX42xWj9ZKdH3nJ3Yshfp6hXooUO9Au         D5Uu5m0f+qTS3hZQyG2QjREH4hKz0IOn5YoXpLkRbFVQcfHrI7FbRKq5s/V/fy9Yx7a2         JfFg=='},
    {'name': 'ARC-Authentication-Results', 'value': 'i=1; mx.google.com;       dkim=pass header.i=@rb.cz header.s=rb header.b=VtvXVKcB;       spf=pass (google.com: domain of info@rb.cz designates 62.168.7.193 as permitted sender) smtp.mailfrom=info@rb.cz;       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=rb.cz'},
    {'name': 'Return-Path', 'value': '<info@rb.cz>'},
    {'name': 'Received', 'value': 'from mailproxy.rb.cz (net02a.rb.cz. [62.168.7.193])        by mx.google.com with ESMTPS id m29-20020a50931d000000b00558dae9339dsi2774937eda.393.2024.01.15.04.02.00        for <prirozenoucestou.objednavky@gmail.com>        (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);        Mon, 15 Jan 2024 04:02:00 -0800 (PST)'},
    {'name': 'Received-SPF', 'value': 'pass (google.com: domain of info@rb.cz designates 62.168.7.193 as permitted sender) client-ip=62.168.7.193;'},
    {'name': 'Authentication-Results', 'value': 'mx.google.com;       dkim=pass header.i=@rb.cz header.s=rb header.b=VtvXVKcB;       spf=pass (google.com: domain of info@rb.cz designates 62.168.7.193 as permitted sender) smtp.mailfrom=info@rb.cz;       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=rb.cz'},
    {'name': 'DKIM-Signature', 'value': 'v=1; a=rsa-sha1; c=simple/simple; d=rb.cz; s=rb; t=1705320120; bh=sOKVBXgQocH7vYf9R9NwA9cP43w=; l=17906; h=From; b=VtvXVKcBOG7pBmMuApjRemZ+lhIE2ANn8lrQAXUu93jG/BkGXuxCIYt4PDxskgE/W\t JqArcPvfa4z9SnC7OzgHWCf/XEc/MfREiXdRvLF4l7rGsQ5MLzg5QqG5I/gRPibUkh\t 47pP7NAZ2INsNpyBM7TlgHe18OtFIOPTNSaB/ZZE='},
    {'name': 'Received', 'value': 'from czcrbp08.rb.cz (unknown [172.18.2.5]) by Forcepoint Email with ESMTP id 12548733C4F5ECC91511 for <prirozenoucestou.objednavky@gmail.com>; Mon, 15 Jan 2024 13:02:00 +0100 (CET)'},
    {'name': 'Received', 'value': 'from mchjb05ap2.rb.cz ([10.237.91.28])          by czcrbp08.rb.cz (IBM Domino Release 10.0.1FP6)          with ESMTP id 2024011513014953-1491385 ;          Mon, 15 Jan 2024 13:01:49 +0100'},
    {'name': 'Date', 'value': 'Mon, 15 Jan 2024 13:01:59 +0100 (CET)'},
    {'name': 'To', 'value': 'prirozenoucestou.objednavky@gmail.com'},
    {'name': 'Message-ID', 'value': '<1295968621.437763.1705320119780@rb.cz>'},
    {'name': 'Subject', 'value': 'Pohyb na účtě'},
    {'name': 'MIME-Version', 'value': '1.0'},
    {'name': 'X-TNEFEvaluated', 'value': '1'},
    {'name': 'From', 'value': 'Raiffeisenbank <info@rb.cz>'},
    {'name': 'Reply-To', 'value': 'Raiffeisenbank <info@rb.cz>'},
    {'name': 'X-FromDomain', 'value': 'rb.cz'},
    {'name': 'X-MIMETrack', 'value': 'Itemize by SMTP Server on CZCRBP08/CRB-PRAHA(Release 10.0.1FP6|September 24, 2020) at 15.01.2024 13:01:49, Serialize by Router on CZCRBP08/CRB-PRAHA(Release 10.0.1FP6|September 24, 2020) at 15.01.2024 13:01:49'},
    {'name': 'Content-Type', 'value': 'multipart/related; boundary="----=_Part_437762_1285639209.1705320119780"'}
]

def test_getval():
    assert orders.getval(mail_data, 'Subject') == 'Pohyb na účtě'

def test_filter_by_subject():
    assert any(orders.filter_by_subject([{'payload': {'headers': mail_data}}], 'Pohyb na účtě'))