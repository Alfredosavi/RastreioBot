import json
from datetime import date
import status
from misc import check_type


def check_update(code, max_retries=3):
    print(' check_update')
    api_type = check_type(code)
    if api_type is None:
            return status.TYPO
    stats = []
    print(api_type)
    try:
        response = api_type.get(code, max_retries)
        result = json.loads(response)
        tabela = result['objeto'][0]['evento']
    except Exception:
        return status.NOT_FOUND
    if len(tabela) < 1:
        return status.NOT_FOUND
    stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    for evento in reversed(tabela):
        try:
            dia0 = int(tabela[len(tabela) - 1]['data'].split('/')[0])
            mes0 = int(tabela[len(tabela) - 1]['data'].split('/')[1])
            ano0 = int(tabela[len(tabela) - 1]['data'].split('/')[2])
            data0 = date(ano0, mes0, dia0)
            dia1 = int(evento['data'].split('/')[0])
            mes1 = int(evento['data'].split('/')[1])
            ano1 = int(evento['data'].split('/')[2])
            data1 = date(ano1, mes1, dia1)
            delta = data1 - data0
        except Exception:
            delta = 0
            pass
        data = evento['data'] + ' ' + evento['hora']
        if delta.days == 1:
            data = data + ' (' + str(delta.days) + ' dia)'
        elif delta.days > 1:
            data = data + ' (' + str(delta.days) + ' dias)'
        try:
            local = evento['unidade']['local']
        except Exception:
            local = False
        situacao = evento['descricao']
        if 'endereço indicado' in evento['descricao']:
            try:
                situacao = (
                    situacao + '\n</b>' +
                    evento['unidade']['endereco']['numero'] + ' ' +
                    evento['unidade']['endereco']['logradouro'] + '\n' +
                    evento['unidade']['endereco']['bairro'] + '<b>'
                )
            except Exception:
                pass
        try:
            observacao = str(evento['destino'][0]['local'])
        except Exception:
            observacao = False
        mensagem = 'Data: ' + data.strip()
        if local:
            mensagem = mensagem + '\nLocal: ' + local.strip().title()
        if situacao:
            mensagem = (
                mensagem + '\nSituação: <b>' +
                situacao.strip() + '</b>'
            )
            if 'objeto entregue ao' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F381')
            elif 'encaminhado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U00002197')
            elif 'postado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F4E6')
        if observacao:
            mensagem = mensagem + '\nObservação: ' + observacao.strip().title()
            if 'liberado sem' in observacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F389')
        stats.append(mensagem)
    return stats
