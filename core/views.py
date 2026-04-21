from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import (
    Cliente, OrdemServico, FotoOS,
    Peca, HistoricoManutencao, FichaMotor
)


# ==========================
# DASHBOARD
# ==========================
@login_required
def dashboard(request):

    query = request.GET.get("q")

    ordens = (
        OrdemServico.objects
        .filter(user=request.user)
        .select_related('cliente')
        .prefetch_related('fotos')
        .order_by('-created_at')
    )

    if query:
        ordens = ordens.filter(
            Q(cliente__nome__icontains=query) |
            Q(modelo_motor__icontains=query)
        )

    status_cores = {
        'PENDENTE': 'secondary',
        'DIAGNOSTICO': 'info',
        'ORCAMENTO_ENVIADO': 'warning',
        'ORCAMENTO_APROVADO': 'primary',
        'ORCAMENTO_REPROVADO': 'danger',
        'MANUTENCAO': 'primary',
        'PECAS': 'warning',
        'FINALIZADO': 'success',
        'ENTREGUE': 'dark',
        'CANCELADO': 'danger',
    }

    colunas = []

    for key, label in OrdemServico.STATUS_CHOICES:
        colunas.append({
            "status_key": key,
            "titulo": label,
            "cor": status_cores.get(key, "secondary"),
            "itens": ordens.filter(status=key)
        })

    return render(request, "dashboard.html", {"colunas": colunas})


# ==========================
# CHECK-IN
# ==========================
@login_required
def checkin(request):

    if request.method == "POST":

        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        modelo = request.POST.get("modelo")
        marca = request.POST.get("marca")
        problema = request.POST.get("descricao")

        cliente, created = Cliente.objects.get_or_create(
            telefone=telefone,
            user=request.user,
            defaults={"nome": nome}
        )

        if not created:
            cliente.nome = nome
            cliente.save()

        os = OrdemServico.objects.create(
            user=request.user,
            cliente=cliente,
            modelo_motor=modelo,
            marca=marca,
            descricao_problema=problema,
        )

        for foto in request.FILES.getlist("fotos"):
            FotoOS.objects.create(os=os, imagem=foto)

        messages.success(request, "Ordem de Serviço criada com sucesso.")
        return redirect("dashboard")

    return render(request, "checkin.html")


# ==========================
# DETALHE OS
# ==========================
@login_required
def os_detail(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    return render(request, "os_detail.html", {"os": os})


# ==========================
# AÇÕES SEGURAS
# ==========================

@require_POST
@login_required
def atualizar_status(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    status = request.POST.get("status")

    if status in dict(OrdemServico.STATUS_CHOICES):
        os.status = status
        os.save()

    return redirect("dashboard")


@require_POST
@login_required
def finalizar_servico(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    os.status = "FINALIZADO"
    os.save()

    messages.success(request, "Serviço finalizado.")
    return redirect("dashboard")


@require_POST
@login_required
def adicionar_peca(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    Peca.objects.create(
        os=os,
        nome=request.POST.get("nome"),
        valor=request.POST.get("valor"),
        foto=request.FILES.get("foto")
    )

    return redirect("os_detail", os_id=os.id)


@require_POST
@login_required
def adicionar_historico(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    HistoricoManutencao.objects.create(
        os=os,
        descricao=request.POST.get("descricao"),
        criado_por=request.user
    )

    return redirect("os_detail", os_id=os.id)


@require_POST
@login_required
def adicionar_foto(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    foto = request.FILES.get("foto")

    if foto:
        FotoOS.objects.create(os=os, imagem=foto)

    return redirect("os_detail", os_id=os.id)


@require_POST
@login_required
def remover_foto(request, foto_id):

    foto = get_object_or_404(
        FotoOS,
        id=foto_id,
        os__user=request.user
    )

    os_id = foto.os.id

    if foto.imagem:
        foto.imagem.delete()

    foto.delete()

    return redirect("os_detail", os_id=os_id)


@require_POST
@login_required
def atualizar_mao_obra(request, os_id):

    os = get_object_or_404(
        OrdemServico,
        id=os_id,
        user=request.user
    )

    try:
        os.valor_mao_obra = float(request.POST.get("valor_mao_obra"))
        os.save()
    except:
        pass

    return redirect("os_detail", os_id=os.id)


# ==========================
# HISTÓRICO
# ==========================
@login_required
def historico_geral(request):

    query = request.GET.get("q")
    status = request.GET.get("status")

    ordens = (
        OrdemServico.objects
        .filter(user=request.user)
        .select_related('cliente')
        .order_by('-created_at')
    )

    if query:
        ordens = ordens.filter(
            Q(cliente__nome__icontains=query) |
            Q(modelo_motor__icontains=query)
        )

    if status:
        ordens = ordens.filter(status=status)

    return render(request, "historico.html", {
        "ordens": ordens,
        "status_choices": OrdemServico.STATUS_CHOICES
    })


# ==========================
# MÉTRICAS
# ==========================
@login_required
def metricas(request):

    periodo = request.GET.get("periodo", "mes")
    hoje = timezone.now()

    if periodo == "semana":
        inicio = hoje - timedelta(days=7)
    elif periodo == "hoje":
        inicio = hoje.replace(hour=0, minute=0, second=0)
    else:
        inicio = hoje.replace(day=1, hour=0, minute=0, second=0)

    # 🔒 SEMPRE filtra por usuário
    ordens_usuario = OrdemServico.objects.filter(user=request.user)

    # 🔍 tenta pegar pelo período
    ordens_periodo = ordens_usuario.filter(created_at__gte=inicio)

    # 🔁 fallback: se não tiver dados no período, usa tudo do usuário
    if not ordens_periodo.exists():
        ordens_periodo = ordens_usuario

    contagem = (
        ordens_periodo
        .values("status")
        .annotate(total=Count("id"))
    )

    contagem_dict = {i["status"]: i["total"] for i in contagem}

    # VISUAL (mantive o seu padrão original)
    visual_map = {
        "PENDENTE": ("secondary", "bi-hourglass"),
        "DIAGNOSTICO": ("info", "bi-search"),
        "ORCAMENTO_ENVIADO": ("warning", "bi-send"),
        "ORCAMENTO_APROVADO": ("primary", "bi-check-circle"),
        "ORCAMENTO_REPROVADO": ("danger", "bi-x-circle"),
        "MANUTENCAO": ("primary", "bi-tools"),
        "PECAS": ("warning", "bi-box-seam"),
        "FINALIZADO": ("success", "bi-check2-all"),
        "ENTREGUE": ("dark", "bi-truck"),
        "CANCELADO": ("danger", "bi-slash-circle"),
    }

    cards = []

    for key, label in OrdemServico.STATUS_CHOICES:
        cor, icone = visual_map.get(key, ("secondary", "bi-circle"))

        cards.append({
            "label": label,
            "total": contagem_dict.get(key, 0),
            "cor": cor,
            "icone": icone
        })

    return render(request, "metricas.html", {
        "cards": cards,
        "periodo": periodo
    })

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

@login_required
def gerar_relatorio(request):

    periodo = request.GET.get("periodo", "mes")
    hoje = timezone.now()

    if periodo == "semana":
        inicio = hoje - timedelta(days=7)
    elif periodo == "hoje":
        inicio = hoje.replace(hour=0, minute=0, second=0)
    else:
        inicio = hoje.replace(day=1, hour=0, minute=0, second=0)

    ordens = OrdemServico.objects.filter(
        user=request.user,
        created_at__gte=inicio
    ).select_related('cliente').order_by('-created_at')

    html_string = render_to_string("relatorio_pdf.html", {
        "ordens": ordens,
        "periodo": periodo
    })

    response = HttpResponse(content_type='application/pdf')
    data_str = timezone.now().strftime("%d_%m_%y")
    filename = f"relatorio_{data_str}.pdf"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    HTML(string=html_string).write_pdf(response)

    return response

# ==========================
# FICHAS MOTOR
# ==========================
@login_required
def fichas_motor(request):

    if request.method == 'POST':
        FichaMotor.objects.create(
            user=request.user,
            potencia=request.POST.get('potencia'),
            tensao=request.POST.get('tensao'),
            tipo=request.POST.get('tipo'),
            marca_modelo=request.POST.get('marca_modelo'),

            numero_ranhuras=request.POST.get('numero_ranhuras'),
            numero_polos=request.POST.get('numero_polos'),
            tipo_enrolamento=request.POST.get('tipo_enrolamento'),

            espiras_por_bobina=request.POST.get('espiras'),
            bitola_fio=request.POST.get('bitola'),
            passo_bobina=request.POST.get('passo'),
            bobinas_por_fase=request.POST.get('bobinas'),

            tipo_ligacao=request.POST.get('ligacao'),
            esquema_fechamento=request.POST.get('esquema'),
        )
        return redirect('fichas_motor')

    fichas = FichaMotor.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'fichas_motor.html', {'fichas': fichas})


@login_required
def ficha_detail(request, id):

    ficha = get_object_or_404(
        FichaMotor,
        id=id,
        user=request.user
    )

    return render(request, 'ficha_detail.html', {'f': ficha})