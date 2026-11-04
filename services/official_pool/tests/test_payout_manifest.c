/* Native FRG payout manifest test. NO wallets, funds, mining or network. */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../jtgrassie/src/frg_payout_manifest.h"

static char a[96], b[96];
static void tohex(const uint8_t x[32], char h[65]) {
    const char *d="0123456789abcdef";
    for (int i=0;i<32;i++){h[i*2]=d[x[i]>>4];h[i*2+1]=d[x[i]&15];}
    h[64]=0;
}
int main(void) {
    a[0]='4'; memset(a+1,'A',94); a[95]=0;
    b[0]='5'; memset(b+1,'B',94); b[95]=0;
    const uint8_t uuid[16]={0xbd},source[32]={7},anchor[32]={3},zero[32]={0};
    frg_payout_recipient_t p[2]={{a,100000000},{b,230000000}};
    uint8_t id[32],digest[32],i2[32],d2[32];
    uint64_t total=0, t2=0;
    assert(!frg_payout_manifest_hash(uuid,source,anchor,150,p,2,12345,id,digest,&total));
    assert(total==330000000);
    char h[65];tohex(id,h);
    assert(!strcmp(h,"c2910adaf0c7efa889b87a465ef8972224f1f93594388e7b4c0bc8e21545ae85"));
    tohex(digest,h);
    assert(!strcmp(h,"8175a57cec0ffb57c9f8a5621c8586668a70ac673e4ee6322a388166c5a31502"));
    assert(!frg_payout_manifest_hash(uuid,source,anchor,150,p,2,12345,i2,d2,&t2));
    assert(!memcmp(id,i2,32)&&!memcmp(digest,d2,32)&&t2==total);
    /* Amount changed: same source-based batch identity, different manifest. */
    p[1].amount_atomic++;
    assert(!frg_payout_manifest_hash(uuid,source,anchor,150,p,2,12345,i2,d2,&t2));
    assert(!memcmp(id,i2,32) && memcmp(digest,d2,32));
    p[1].amount_atomic--;
    uint8_t other[32]={8};
    assert(!frg_payout_manifest_hash(uuid,other,anchor,150,p,2,12345,i2,d2,&t2));
    assert(memcmp(id,i2,32));
    #define BAD(list,count,fee) assert(frg_payout_manifest_hash(uuid,source,anchor,150,list,count,fee,i2,d2,&t2)==EINVAL)
    frg_payout_recipient_t reversed[2]={{b,230000000},{a,100000000}};
    frg_payout_recipient_t duplicate[2]={{a,1},{a,2}};
    frg_payout_recipient_t overflow[2]={{a,UINT64_MAX},{b,1}};
    frg_payout_recipient_t invalid[1]={{"4O00000",1}};
    frg_payout_recipient_t empty[1]={{a,0}};
    BAD(reversed,2,0);BAD(duplicate,2,0);BAD(overflow,2,0);
    BAD(invalid,1,0);BAD(empty,1,0);BAD(p,0,0);BAD(p,2,330000001);
    BAD(p,26,0);
    assert(frg_payout_manifest_hash(uuid,zero,anchor,150,p,2,0,i2,d2,&t2)==EINVAL);
    assert(frg_payout_manifest_hash(uuid,source,zero,150,p,2,0,i2,d2,&t2)==EINVAL);
    assert(frg_payout_manifest_hash(uuid,source,anchor,59,p,2,0,i2,d2,&t2)==EINVAL);
    assert(frg_payout_manifest_hash(uuid,source,anchor,150,p,2,0,i2,i2,&t2)==EINVAL);
    /* Invalid attempts never change caller's result buffers. */
    memset(i2,0xab,32);memset(d2,0xcd,32);t2=UINT64_MAX;
    BAD(duplicate,2,0);
    for(int j=0;j<32;j++){assert(i2[j]==0xab);assert(d2[j]==0xcd);}
    assert(t2==UINT64_MAX);
    puts("PASS: native SHA256 payout manifest, deterministic ID and fail-closed replay/overflow/fee guards");
    return 0;
}
