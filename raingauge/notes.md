
## AWS Security Policies for SimpleDB

there is a security policy attached:
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sdb:*",
            "Resource": "arn:aws:sdb:*:973829276751:domain/*"
        }
    ]
}

http://docs.aws.amazon.com/AmazonSimpleDB/latest/DeveloperGuide/UsingIAMWithSDB.html


## Testing

    socat -d -d pty,raw,echo=0 pty,raw,echo=0


## Sample data

    #3410#rm
    3410;1;3
    1;093%;01;2.3917;0.014
    05.03.15;13:18:40;S;1;0;1;0;0;+32.9;0000;000.00
    05.03.15;13:19:40;I;1;0;1;0;0;+33.2;0000;000.00
    05.03.15;13:20:40;I;1;0;1;0;0;+33.5;0000;000.00
    05.03.15;13:21:40;I;1;0;1;0;0;+33.7;0000;000.00
    +3410+
