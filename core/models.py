import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User


class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.telefone}"


class OrdemServico(models.Model):

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('DIAGNOSTICO', 'Em Diagnóstico'),
        ('ORCAMENTO_ENVIADO', 'Orçamento Enviado'),
        ('ORCAMENTO_APROVADO', 'Orçamento Aprovado'),
        ('ORCAMENTO_REPROVADO', 'Orçamento Reprovado'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('PECAS', 'Aguardando Peças'),
        ('FINALIZADO', 'Finalizado'),
        ('ENTREGUE', 'Entregue'),
        ('CANCELADO', 'Cancelado'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ordens'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='ordens'
    )

    modelo_motor = models.CharField(max_length=255)
    marca = models.CharField(max_length=255)
    descricao_problema = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        db_index=True
    )

    valor_mao_obra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    observacoes_internas = models.TextField(blank=True, null=True)

    tecnico_responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OS #{self.id} - {self.cliente.nome}"

    @property
    def total_pecas(self):
        total = self.pecas.aggregate(total=Sum('valor'))['total']
        return total or Decimal('0.00')

    @property
    def valor_total(self):
        return self.total_pecas + self.valor_mao_obra


class FotoOS(models.Model):
    os = models.ForeignKey(
        OrdemServico,
        related_name='fotos',
        on_delete=models.CASCADE
    )

    imagem = models.ImageField(upload_to='os_fotos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Foto OS {self.os.id}"


class Peca(models.Model):
    os = models.ForeignKey(
        OrdemServico,
        related_name='pecas',
        on_delete=models.CASCADE
    )

    nome = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    foto = models.ImageField(upload_to='pecas_fotos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - OS {self.os.id}"


class HistoricoManutencao(models.Model):
    os = models.ForeignKey(
        OrdemServico,
        related_name='historico',
        on_delete=models.CASCADE
    )

    descricao = models.TextField()

    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Histórico OS {self.os.id}"

# models.py

class FichaMotor(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Identificação
    potencia = models.CharField(max_length=50)
    tensao = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)
    marca_modelo = models.CharField(max_length=255)

    # Construtivo
    numero_ranhuras = models.IntegerField()
    numero_polos = models.IntegerField()
    tipo_enrolamento = models.CharField(max_length=100)

    # Bobinagem
    espiras_por_bobina = models.IntegerField()
    bitola_fio = models.CharField(max_length=50)
    passo_bobina = models.CharField(max_length=50)
    bobinas_por_fase = models.IntegerField()

    # Ligação
    tipo_ligacao = models.CharField(max_length=50)
    esquema_fechamento = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.marca_modelo